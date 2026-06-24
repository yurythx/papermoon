"""
Targeted integration tests for uncovered lines in:
- apps/subscriptions/views_admin.py  (filter params, detail, renew, cancel)
- apps/notifications/views.py  (paginated list, no-profile NotFound)
- shared/views.py  (health check error paths: DB failure, Redis failure, Celery failure)
"""

from unittest.mock import patch
import uuid

from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.customers.models import Customer, CustomerProfile
from apps.notifications.models import Notification
from apps.products.models import Pricing, Product
from apps.subscriptions.models import License, Subscription

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc(n: int = 0) -> str:
    d = f"{uuid.uuid4().int % 10**14:014d}"
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def _make_product(slug: str):
    product = Product.objects.create(name="Test Product", slug=slug)
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
    return product, pricing


def _make_customer(doc: str | None = None) -> Customer:
    return Customer.objects.create(company_name="Test Co", document=doc or _doc())


def _make_subscription(customer: Customer, product: Product, pricing: Pricing) -> Subscription:
    import datetime

    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now() + datetime.timedelta(days=30),
    )
    License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + datetime.timedelta(days=30),
    )
    return sub


def _make_notification(customer: Customer, status=Notification.Status.PENDING) -> Notification:
    return Notification.objects.create(
        channel=Notification.Channel.IN_APP,
        event_type="test.event",
        recipient=str(customer.id),
        subject="Test",
        body="Body",
        status=status,
    )


# ---------------------------------------------------------------------------
# Admin subscription list — filter params (lines 45, 47)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminSubscriptionListFilters:
    def test_filter_by_customer_id_returns_only_that_customer(self, admin_client):
        product, pricing = _make_product(f"filt-cust-{uuid.uuid4().hex[:4]}")
        customer_a = _make_customer()
        customer_b = _make_customer()
        sub_a = _make_subscription(customer_a, product, pricing)
        sub_b = _make_subscription(customer_b, product, pricing)

        resp = admin_client.get(f"/api/v1/admin/subscriptions/?customer_id={customer_a.id}")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["data"]["results"]]
        assert str(sub_a.id) in ids
        assert str(sub_b.id) not in ids

    def test_filter_by_status_returns_matching_subscriptions(self, admin_client):
        product, pricing = _make_product(f"filt-status-{uuid.uuid4().hex[:4]}")
        customer = _make_customer()
        active_sub = _make_subscription(customer, product, pricing)

        resp = admin_client.get("/api/v1/admin/subscriptions/?status=active")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["data"]["results"]]
        assert str(active_sub.id) in ids


# ---------------------------------------------------------------------------
# Admin subscription detail (lines 72-74, 83)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminSubscriptionDetail:
    def test_get_returns_subscription(self, admin_client):
        product, pricing = _make_product(f"detail-{uuid.uuid4().hex[:4]}")
        customer = _make_customer()
        sub = _make_subscription(customer, product, pricing)

        resp = admin_client.get(f"/api/v1/admin/subscriptions/{sub.id}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(sub.id)

    def test_get_unknown_id_returns_404(self, admin_client):
        resp = admin_client.get(f"/api/v1/admin/subscriptions/{uuid.uuid4()}/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Admin subscription renew (lines 105-106)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminSubscriptionRenew:
    def test_renew_suspended_subscription(self, admin_client):
        product, pricing = _make_product(f"renew-{uuid.uuid4().hex[:4]}")
        customer = _make_customer()
        sub = _make_subscription(customer, product, pricing)
        sub.status = Subscription.Status.SUSPENDED
        sub.save()

        with patch("apps.support.client.ChatwootClient"):
            resp = admin_client.post(f"/api/v1/admin/subscriptions/{sub.id}/renew/")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "active"


# ---------------------------------------------------------------------------
# Admin subscription cancel (lines 116-118)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminSubscriptionCancel:
    def test_cancel_active_subscription(self, admin_client):
        product, pricing = _make_product(f"cancel-{uuid.uuid4().hex[:4]}")
        customer = _make_customer()
        sub = _make_subscription(customer, product, pricing)

        with patch("apps.support.client.ChatwootClient"):
            resp = admin_client.post(
                f"/api/v1/admin/subscriptions/{sub.id}/cancel/",
                {"reason": "test cancel"},
                format="json",
            )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "cancelled"


# ---------------------------------------------------------------------------
# notifications/views.py — paginated list (lines 58-66), no-profile (line 29)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestNotificationsViewCoverage:
    def _make_customer_with_client(self) -> tuple[APIClient, Customer]:
        email = f"notif_{uuid.uuid4().hex[:6]}@x.com"
        user = CustomUser.objects.create_user(
            username=email.split("@")[0], email=email, password="pass"
        )
        customer = Customer.objects.create(company_name="Notif Co", document=_doc())
        CustomerProfile.objects.create(
            user=user, customer=customer, role=CustomerProfile.Role.OWNER
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": email, "password": "pass"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        return client, customer

    def test_paginated_list_returns_page_data(self):
        client, customer = self._make_customer_with_client()
        # Create 5 in-app notifications
        for _ in range(5):
            _make_notification(customer)

        resp = client.get("/api/v1/client/notifications/?page=1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "results" in data
        assert "num_pages" in data
        assert "count" in data

    def test_paginated_list_invalid_page_falls_back_to_1(self):
        client, customer = self._make_customer_with_client()
        _make_notification(customer)

        resp = client.get("/api/v1/client/notifications/?page=abc")
        assert resp.status_code == 200

    def test_no_profile_returns_404(self, api_client, regular_user):
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.get("/api/v1/client/notifications/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# shared/views.py — health check error paths (lines 21-22, 27-28, 35-36)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHealthCheckErrorPaths:
    def test_db_failure_returns_error_status(self, api_client):
        # Patch the connection OBJECT within shared.views so the real test DB is unaffected
        from unittest.mock import MagicMock

        mock_conn = MagicMock()
        mock_conn.ensure_connection.side_effect = Exception("DB down")
        with patch("shared.views.connection", mock_conn):
            resp = api_client.get("/health/")
        assert resp.status_code == 503
        # 503 is an error response — renderer places payload in "error" not "data"
        assert resp.json()["error"]["db"] == "error"

    def test_redis_failure_returns_error_status(self, api_client):
        # Patch only the cache object within shared.views to avoid breaking throttle cache
        from unittest.mock import MagicMock

        mock_cache = MagicMock()
        mock_cache.set.side_effect = Exception("Redis down")
        with patch("shared.views.cache", mock_cache):
            resp = api_client.get("/health/")
        assert resp.status_code == 503
        assert resp.json()["error"]["redis"] == "error"

    def test_celery_failure_returns_error(self, api_client):
        # Patch at the point where celery is imported inside the view function
        with patch("celery.current_app.control.inspect", side_effect=Exception("Celery down")):
            resp = api_client.get("/health/")
        data = resp.json().get("error") or resp.json().get("data") or {}
        assert data.get("celery") == "error"
