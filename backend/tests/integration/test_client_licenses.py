"""Integration tests for GET /api/v1/client/licenses/ and /api/v1/client/licenses/<pk>/."""

import datetime
from unittest.mock import patch

from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.customers.models import Customer, CustomerProfile
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.models import Subscription

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_customer(doc: str) -> Customer:
    return Customer.objects.create(company_name=f"Corp {doc[:4]}", document=doc)


def _make_product_with_services(slug: str, services: tuple = ("n8n",)):
    product = Product.objects.create(name=slug, slug=slug)
    for key in services:
        ServiceComponent.objects.create(product=product, service_key=key)
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="199.00")
    return product, pricing


def _make_subscription(customer: Customer, product: Product, pricing: Pricing) -> Subscription:
    from apps.subscriptions.commands import CreateSubscriptionCommand

    with (
        patch("apps.support.client.ChatwootClient"),
        patch("apps.provisioning.meta_api.MetaWhatsAppProvisioner.provision", return_value="x"),
        patch("apps.provisioning.n8n.N8nProvisioner.provision", return_value="y"),
    ):
        return CreateSubscriptionCommand().execute(
            customer_id=customer.id,
            product_id=product.id,
            pricing_id=pricing.id,
        )


def _authenticated_client(email: str, password: str) -> APIClient:
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
    return client


def _setup_user_with_license(doc: str, services: tuple = ("n8n",)):
    """Return (APIClient, customer, subscription) for a fresh owner user."""
    slug = f"lic-{doc[:4]}"
    product, pricing = _make_product_with_services(slug, services)
    customer = _make_customer(doc)
    user = CustomUser.objects.create_user(
        username=doc[:6], email=f"{doc[:6]}@lictest.com", password="pass1234"
    )
    CustomerProfile.objects.create(user=user, customer=customer, role="owner")
    sub = _make_subscription(customer, product, pricing)
    client = _authenticated_client(f"{doc[:6]}@lictest.com", "pass1234")
    return client, customer, sub


# ---------------------------------------------------------------------------
# GET /api/v1/client/licenses/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientLicenseList:
    def test_returns_own_licenses(self):
        client, customer, sub = _setup_user_with_license("40.000.000/0001-40")
        resp = client.get("/api/v1/client/licenses/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert any(item["id"] == str(sub.license.id) for item in data)

    def test_response_shape_contains_required_fields(self):
        client, _, sub = _setup_user_with_license("41.000.000/0001-41")
        resp = client.get("/api/v1/client/licenses/")
        item = resp.json()["data"][0]
        for field in (
            "id",
            "key",
            "status",
            "valid_from",
            "valid_until",
            "days_remaining",
            "product_name",
            "product_slug",
            "subscription_id",
            "subscription_status",
            "billing_cycle",
            "amount",
            "services",
            "created_at",
        ):
            assert field in item, f"Missing field: {field}"

    def test_days_remaining_is_non_negative_integer(self):
        client, _, sub = _setup_user_with_license("42.000.000/0001-42")
        resp = client.get("/api/v1/client/licenses/")
        days = resp.json()["data"][0]["days_remaining"]
        assert isinstance(days, int)
        assert days >= 0

    def test_services_list_matches_product_components(self):
        client, _, sub = _setup_user_with_license(
            "43.000.000/0001-43", services=("n8n", "chatwoot")
        )
        resp = client.get("/api/v1/client/licenses/")
        services = resp.json()["data"][0]["services"]
        keys = {s["service_key"] for s in services}
        assert keys == {"n8n", "chatwoot"}

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get("/api/v1/client/licenses/")
        assert resp.status_code == 401

    def test_does_not_leak_other_customer_licenses(self):
        client, _, _ = _setup_user_with_license("44.000.000/0001-44")
        # Create an unrelated customer's license
        other_customer = _make_customer("45.000.000/0001-45")
        product, pricing = _make_product_with_services("other-lic-45")
        _make_subscription(other_customer, product, pricing)

        resp = client.get("/api/v1/client/licenses/")
        data = resp.json()["data"]
        # Only the calling user's licenses should appear — 1, not 2
        assert len(data) == 1

    def test_expired_license_shows_zero_days_remaining(self):
        client, _, sub = _setup_user_with_license("46.000.000/0001-46")
        # Force license to expired state
        license_obj = sub.license
        license_obj.valid_until = timezone.now() - datetime.timedelta(days=1)
        license_obj.save(update_fields=["valid_until"])

        resp = client.get("/api/v1/client/licenses/")
        days = resp.json()["data"][0]["days_remaining"]
        assert days == 0


# ---------------------------------------------------------------------------
# GET /api/v1/client/licenses/<pk>/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientLicenseDetail:
    def test_returns_own_license_detail(self):
        client, _, sub = _setup_user_with_license("47.000.000/0001-47")
        license_id = str(sub.license.id)
        resp = client.get(f"/api/v1/client/licenses/{license_id}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == license_id

    def test_detail_has_same_shape_as_list(self):
        client, _, sub = _setup_user_with_license("48.000.000/0001-48")
        license_id = str(sub.license.id)
        resp = client.get(f"/api/v1/client/licenses/{license_id}/")
        item = resp.json()["data"]
        for field in (
            "id",
            "key",
            "status",
            "days_remaining",
            "product_name",
            "product_slug",
            "services",
        ):
            assert field in item, f"Missing field: {field}"

    def test_returns_404_for_unknown_license(self):
        from uuid import uuid4

        client, _, _ = _setup_user_with_license("49.000.000/0001-49")
        resp = client.get(f"/api/v1/client/licenses/{uuid4()}/")
        assert resp.status_code == 404

    def test_tenant_isolation_returns_404_for_other_customer_license(self):
        """A user must not be able to retrieve another tenant's license."""
        client, _, _ = _setup_user_with_license("50.000.000/0001-50")
        other_customer = _make_customer("51.000.000/0001-51")
        product, pricing = _make_product_with_services("isolation-51")
        other_sub = _make_subscription(other_customer, product, pricing)

        resp = client.get(f"/api/v1/client/licenses/{other_sub.license.id}/")
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, api_client):
        from uuid import uuid4

        resp = api_client.get(f"/api/v1/client/licenses/{uuid4()}/")
        assert resp.status_code == 401
