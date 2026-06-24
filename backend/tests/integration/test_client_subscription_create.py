"""Integration tests for subscription self-service endpoints not yet covered.

Covers:
- POST /api/v1/client/subscriptions/  (create via catalog)
- GET  /api/v1/subscriptions/validate-license/?key=xxx
- No-profile PermissionDenied path
- Missing pricing_id validation in change-plan
"""

import uuid

from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.customers.models import Customer, CustomerProfile
from apps.products.models import Pricing, Product
from apps.subscriptions.models import Subscription
from tests.conftest import create_active_license


def _make_client_with_profile(email_suffix: str) -> tuple[APIClient, Customer]:
    email = f"selfserve_{email_suffix}@test.com"
    user = CustomUser.objects.create_user(
        username=f"ss_{email_suffix}", email=email, password="pass1234"
    )
    doc = f"{uuid.uuid4().int % 10**14:014d}"
    doc_fmt = f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:14]}"
    customer = Customer.objects.create(company_name="Self Serve Co", document=doc_fmt)
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)

    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/", {"email": email, "password": "pass1234"}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
    return client, customer


def _make_product_and_pricing() -> tuple[Product, Pricing]:
    slug = f"prod-{uuid.uuid4().hex[:6]}"
    product = Product.objects.create(name="Test Plan", slug=slug, is_active=True)
    pricing = Pricing.objects.create(
        product=product, billing_cycle="monthly", amount="49.00", is_active=True
    )
    return product, pricing


# ---------------------------------------------------------------------------
# POST /api/v1/client/subscriptions/ — self-service subscribe
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientSubscriptionCreate:
    URL = "/api/v1/client/subscriptions/"

    def test_creates_subscription_with_valid_product_and_pricing(self):
        client, customer = _make_client_with_profile("create1")
        product, pricing = _make_product_and_pricing()

        resp = client.post(
            self.URL,
            {"product_id": str(product.id), "pricing_id": str(pricing.id)},
            format="json",
        )
        assert resp.status_code == 201
        assert Subscription.objects.filter(customer=customer, product=product).exists()

    def test_missing_product_id_returns_400(self):
        client, _ = _make_client_with_profile("create2")
        _, pricing = _make_product_and_pricing()

        resp = client.post(self.URL, {"pricing_id": str(pricing.id)}, format="json")
        assert resp.status_code == 400

    def test_missing_pricing_id_returns_400(self):
        client, _ = _make_client_with_profile("create3")
        product, _ = _make_product_and_pricing()

        resp = client.post(self.URL, {"product_id": str(product.id)}, format="json")
        assert resp.status_code == 400

    def test_unknown_product_returns_400(self):
        client, _ = _make_client_with_profile("create4")
        _, pricing = _make_product_and_pricing()

        resp = client.post(
            self.URL,
            {"product_id": str(uuid.uuid4()), "pricing_id": str(pricing.id)},
            format="json",
        )
        assert resp.status_code == 400

    def test_unknown_pricing_returns_400(self):
        client, _ = _make_client_with_profile("create5")
        product, _ = _make_product_and_pricing()

        resp = client.post(
            self.URL,
            {"product_id": str(product.id), "pricing_id": str(uuid.uuid4())},
            format="json",
        )
        assert resp.status_code == 400

    def test_pricing_from_different_product_returns_400(self):
        client, _ = _make_client_with_profile("create6")
        product, _ = _make_product_and_pricing()
        other_product, other_pricing = _make_product_and_pricing()

        resp = client.post(
            self.URL,
            {"product_id": str(product.id), "pricing_id": str(other_pricing.id)},
            format="json",
        )
        assert resp.status_code == 400

    def test_duplicate_active_subscription_returns_400(self):
        import datetime

        client, customer = _make_client_with_profile("create7")
        product, pricing = _make_product_and_pricing()

        # Create existing active subscription
        Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=timezone.now(),
            expires_at=timezone.now() + datetime.timedelta(days=30),
        )

        resp = client.post(
            self.URL,
            {"product_id": str(product.id), "pricing_id": str(pricing.id)},
            format="json",
        )
        assert resp.status_code == 400

    def test_inactive_product_returns_400(self):
        client, _ = _make_client_with_profile("create8")
        product = Product.objects.create(
            name="Inactive Plan",
            slug=f"inactive-{uuid.uuid4().hex[:6]}",
            is_active=False,
        )
        pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="49.00")

        resp = client.post(
            self.URL,
            {"product_id": str(product.id), "pricing_id": str(pricing.id)},
            format="json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# No-profile PermissionDenied path
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientSubscriptionNoProfile:
    def test_list_with_no_profile_raises_permission_denied(self, api_client, regular_user):
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.get("/api/v1/client/subscriptions/")
        assert resp.status_code == 403

    def test_post_with_no_profile_raises_permission_denied(self, api_client, regular_user):
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        product, pricing = _make_product_and_pricing()
        resp = api_client.post(
            "/api/v1/client/subscriptions/",
            {"product_id": str(product.id), "pricing_id": str(pricing.id)},
            format="json",
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# change-plan — missing pricing_id
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientChangePlanValidation:
    def test_missing_pricing_id_returns_400(self):
        import datetime

        client, customer = _make_client_with_profile("changeplan1")
        product, pricing = _make_product_and_pricing()
        sub = Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=timezone.now(),
            expires_at=timezone.now() + datetime.timedelta(days=30),
        )

        resp = client.post(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan/",
            {},
            format="json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/subscriptions/validate-license/?key=xxx
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateLicenseEndpoint:
    URL = "/api/v1/client/subscriptions/validate-license/"

    def test_missing_key_returns_400(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 400
        # error responses: renderer puts payload in "error", not "data"
        assert resp.json()["error"]["reason"] == "key_required"

    def test_unknown_key_returns_404_and_caches_result(self, api_client):
        from django.core.cache import cache

        cache.clear()
        fake_key = "this_key_does_not_exist"
        resp = api_client.get(f"{self.URL}?key={fake_key}")
        assert resp.status_code == 404
        assert resp.json()["error"]["valid"] is False
        assert resp.json()["error"]["reason"] == "not_found"

    def test_valid_license_returns_valid_true(self, api_client, customer):
        from django.core.cache import cache

        cache.clear()
        license_obj = create_active_license(customer)

        resp = api_client.get(f"{self.URL}?key={license_obj.key}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["valid"] is True
        assert "status" in data
        assert "product" in data

    def test_cache_hit_returns_cached_result(self, api_client, customer):
        import hashlib

        from django.core.cache import cache

        cache.clear()
        license_obj = create_active_license(customer)

        # Pre-populate cache
        cache_key = f"license:{hashlib.sha256(license_obj.key.encode()).hexdigest()[:32]}"
        cache.set(cache_key, {"valid": True, "cached": True}, timeout=60)

        resp = api_client.get(f"{self.URL}?key={license_obj.key}")
        assert resp.status_code == 200
        assert resp.json()["data"].get("cached") is True
