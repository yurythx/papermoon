"""Integration tests for Subscription, License and ServiceAccess."""

from unittest.mock import patch

import pytest

from apps.customers.models import Customer, CustomerProfile
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.models import License, ServiceAccess, Subscription

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_product(slug="test-product", services=("chatwoot", "n8n")):
    product = Product.objects.create(name="Test Product", slug=slug)
    for key in services:
        ServiceComponent.objects.create(product=product, service_key=key)
    pricing = Pricing.objects.create(
        product=product, billing_cycle="monthly", amount="299.00", trial_days=0
    )
    return product, pricing


def _make_customer(doc="10.000.000/0001-10"):
    return Customer.objects.create(company_name="Sub Corp", document=doc)


def _make_subscription(customer, product, pricing):
    from apps.subscriptions.commands import CreateSubscriptionCommand

    with (
        patch("apps.support.client.ChatwootClient"),
        patch("apps.provisioning.meta_api.MetaWhatsAppProvisioner.provision", return_value="ext_1"),
        patch("apps.provisioning.n8n.N8nProvisioner.provision", return_value="ext_2"),
    ):
        return CreateSubscriptionCommand().execute(
            customer_id=customer.id,
            product_id=product.id,
            pricing_id=pricing.id,
        )


# ---------------------------------------------------------------------------
# CreateSubscriptionCommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateSubscription:
    def test_creates_subscription_license_and_service_accesses(self):
        product, pricing = _make_product(slug="create-test", services=("chatwoot", "n8n"))
        customer = _make_customer("11.000.000/0001-11")
        sub = _make_subscription(customer, product, pricing)

        assert sub.status == Subscription.Status.ACTIVE
        assert License.objects.filter(subscription=sub).count() == 1
        license_obj = sub.license
        accesses = ServiceAccess.objects.filter(license=license_obj)
        assert accesses.count() == 2
        assert set(accesses.values_list("service_key", flat=True)) == {"chatwoot", "n8n"}

    def test_emits_subscription_created_outbox_event(self):
        from shared.models import OutboxEvent

        product, pricing = _make_product(slug="outbox-test")
        customer = _make_customer("12.000.000/0001-12")
        _make_subscription(customer, product, pricing)
        assert OutboxEvent.objects.filter(event_type="subscription.created").exists()

    def test_trial_pricing_sets_trial_status(self):
        product = Product.objects.create(name="Trial Product", slug="trial-product")
        ServiceComponent.objects.create(product=product, service_key="n8n")
        pricing = Pricing.objects.create(
            product=product, billing_cycle="monthly", amount="0.00", trial_days=14
        )
        customer = _make_customer("13.000.000/0001-13")
        sub = _make_subscription(customer, product, pricing)
        assert sub.status == Subscription.Status.TRIAL

    def test_license_key_is_unique(self):
        product, pricing = _make_product(slug="unique-key", services=("n8n",))
        c1 = _make_customer("14.000.000/0001-14")
        c2 = _make_customer("15.000.000/0001-15")
        sub1 = _make_subscription(c1, product, pricing)
        sub2 = _make_subscription(c2, product, pricing)
        assert sub1.license.key != sub2.license.key


# ---------------------------------------------------------------------------
# SuspendSubscriptionCommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSuspendSubscription:
    def test_suspend_changes_status_and_service_accesses(self):
        from apps.subscriptions.commands import SuspendSubscriptionCommand

        product, pricing = _make_product(slug="suspend-test")
        customer = _make_customer("16.000.000/0001-16")
        sub = _make_subscription(customer, product, pricing)
        # Force accesses to active for the test
        sub.license.service_accesses.update(status=ServiceAccess.Status.ACTIVE)

        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(sub.id, reason="test")

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.SUSPENDED
        assert (
            sub.license.service_accesses.filter(status=ServiceAccess.Status.SUSPENDED).count() == 2
        )

    def test_suspend_emits_outbox_event(self):
        from apps.subscriptions.commands import SuspendSubscriptionCommand
        from shared.models import OutboxEvent

        product, pricing = _make_product(slug="suspend-outbox")
        customer = _make_customer("17.000.000/0001-17")
        sub = _make_subscription(customer, product, pricing)

        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(sub.id)

        assert OutboxEvent.objects.filter(event_type="subscription.suspended").exists()


# ---------------------------------------------------------------------------
# RenewSubscriptionCommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRenewSubscription:
    def test_renew_extends_expires_at(self):
        from apps.subscriptions.commands import RenewSubscriptionCommand

        product, pricing = _make_product(slug="renew-test")
        customer = _make_customer("18.000.000/0001-18")
        sub = _make_subscription(customer, product, pricing)
        original_expiry = sub.expires_at

        RenewSubscriptionCommand().execute(sub.id)

        sub.refresh_from_db()
        assert sub.expires_at > original_expiry
        assert sub.status == Subscription.Status.ACTIVE

    def test_renew_reactivates_suspended_service_accesses(self):
        from apps.subscriptions.commands import RenewSubscriptionCommand, SuspendSubscriptionCommand

        product, pricing = _make_product(slug="renew-reactivate")
        customer = _make_customer("19.000.000/0001-19")
        sub = _make_subscription(customer, product, pricing)
        sub.license.service_accesses.update(status=ServiceAccess.Status.ACTIVE)

        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(sub.id)

        RenewSubscriptionCommand().execute(sub.id)

        assert sub.license.service_accesses.filter(status=ServiceAccess.Status.ACTIVE).count() == 2


# ---------------------------------------------------------------------------
# ExpireSubscriptionCommand (state machine)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestExpireSubscription:
    def test_active_to_grace_period(self):
        from apps.subscriptions.commands import ExpireSubscriptionCommand

        product, pricing = _make_product(slug="expire-grace")
        customer = _make_customer("20.000.000/0001-20")
        sub = _make_subscription(customer, product, pricing)

        ExpireSubscriptionCommand().execute(sub.id)

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.GRACE_PERIOD

    def test_grace_period_to_expired(self):
        from apps.subscriptions.commands import ExpireSubscriptionCommand
        from shared.models import OutboxEvent

        product, pricing = _make_product(slug="expire-final", services=("n8n",))
        customer = _make_customer("21.000.000/0001-21")
        sub = _make_subscription(customer, product, pricing)

        # First call: active → grace_period
        ExpireSubscriptionCommand().execute(sub.id)
        # Second call: grace_period → expired
        ExpireSubscriptionCommand().execute(sub.id)

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.EXPIRED
        assert OutboxEvent.objects.filter(event_type="subscription.expired").exists()

    def test_expired_license_is_invalid(self):
        from apps.subscriptions.commands import ExpireSubscriptionCommand

        product, pricing = _make_product(slug="invalid-license", services=("n8n",))
        customer = _make_customer("22.000.000/0001-22")
        sub = _make_subscription(customer, product, pricing)
        ExpireSubscriptionCommand().execute(sub.id)  # → grace
        ExpireSubscriptionCommand().execute(sub.id)  # → expired

        sub.refresh_from_db()
        assert sub.license.is_valid() is False


# ---------------------------------------------------------------------------
# Admin API endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminSubscriptionEndpoints:
    def test_admin_can_create_subscription(self, admin_client):
        product, pricing = _make_product(slug="admin-create", services=("n8n",))
        customer = _make_customer("23.000.000/0001-23")
        resp = admin_client.post(
            "/api/v1/admin/subscriptions/",
            {
                "customer_id": str(customer.id),
                "product_id": str(product.id),
                "pricing_id": str(pricing.id),
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "active"
        assert "license" in data

    def test_admin_can_list_subscriptions(self, admin_client):
        product, pricing = _make_product(slug="admin-list", services=("n8n",))
        customer = _make_customer("24.000.000/0001-24")
        _make_subscription(customer, product, pricing)
        resp = admin_client.get("/api/v1/admin/subscriptions/")
        assert resp.status_code == 200

    def test_admin_can_suspend_subscription(self, admin_client):
        product, pricing = _make_product(slug="admin-suspend", services=("n8n",))
        customer = _make_customer("25.000.000/0001-25")
        sub = _make_subscription(customer, product, pricing)
        with patch("apps.support.client.ChatwootClient"):
            resp = admin_client.post(
                f"/api/v1/admin/subscriptions/{sub.id}/suspend/",
                {"reason": "test"},
                format="json",
            )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "suspended"

    def test_non_admin_cannot_access_admin_endpoints(self, customer_client):
        resp = customer_client.get("/api/v1/admin/subscriptions/")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Client API endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientSubscriptionEndpoints:
    def _setup(self, doc="26.000.000/0001-26"):
        from apps.accounts.models import CustomUser

        product, pricing = _make_product(slug=f"client-{doc[:4]}", services=("n8n",))
        customer = _make_customer(doc)
        user = CustomUser.objects.create_user(
            username=doc[:6], email=f"{doc[:6]}@test.com", password="pass123"
        )
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")
        sub = _make_subscription(customer, product, pricing)

        from rest_framework.test import APIClient

        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "pass123"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        return client, customer, sub

    def test_client_can_list_own_subscriptions(self):
        client, customer, sub = self._setup("27.000.000/0001-27")
        resp = client.get("/api/v1/client/subscriptions/")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()["data"]]
        assert str(sub.id) in ids

    def test_client_can_view_subscription_detail(self):
        client, customer, sub = self._setup("28.000.000/0001-28")
        resp = client.get(f"/api/v1/client/subscriptions/{sub.id}/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "license" in data
        assert "service_accesses" in data["license"]

    def test_client_cannot_see_other_customer_subscription(self):
        client, _, _ = self._setup("29.000.000/0001-29")
        product, pricing = _make_product(slug="other-sub", services=("n8n",))
        other_customer = _make_customer("30.000.000/0001-30")
        other_sub = _make_subscription(other_customer, product, pricing)
        resp = client.get(f"/api/v1/client/subscriptions/{other_sub.id}/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# ServiceAccess CRUD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestServiceAccessCRUD:
    def test_admin_can_list_service_accesses(self, admin_client):
        product, pricing = _make_product(slug="sa-list", services=("chatwoot", "n8n"))
        customer = _make_customer("31.000.000/0001-31")
        sub = _make_subscription(customer, product, pricing)
        resp = admin_client.get(f"/api/v1/admin/subscriptions/{sub.id}/services/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_admin_can_add_service_to_existing_subscription(self, admin_client):
        product, pricing = _make_product(slug="sa-add", services=("n8n",))
        customer = _make_customer("32.000.000/0001-32")
        sub = _make_subscription(customer, product, pricing)
        resp = admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/services/",
            {"service_key": "chatwoot"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["service_key"] == "chatwoot"
        assert resp.json()["data"]["status"] == "provisioning"

    def test_duplicate_service_returns_400(self, admin_client):
        product, pricing = _make_product(slug="sa-dup", services=("n8n",))
        customer = _make_customer("33.000.000/0001-33")
        sub = _make_subscription(customer, product, pricing)
        resp = admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/services/",
            {"service_key": "n8n"},
            format="json",
        )
        assert resp.status_code == 400

    def test_admin_can_reprovision_failed_service(self, admin_client):
        from shared.models import OutboxEvent

        product, pricing = _make_product(slug="sa-reprovision", services=("n8n",))
        customer = _make_customer("34.000.000/0001-34")
        sub = _make_subscription(customer, product, pricing)
        sa = ServiceAccess.objects.filter(license=sub.license).first()
        sa.status = ServiceAccess.Status.FAILED
        sa.error = "timeout"
        sa.save()

        resp = admin_client.post(f"/api/v1/admin/service-accesses/{sa.id}/reprovision/")
        assert resp.status_code == 200
        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.PROVISIONING
        assert OutboxEvent.objects.filter(event_type="service_access.provision").exists()

    def test_reprovision_active_service_returns_400(self, admin_client):
        product, pricing = _make_product(slug="sa-reprov-active", services=("n8n",))
        customer = _make_customer("35.000.000/0001-35")
        sub = _make_subscription(customer, product, pricing)
        sa = ServiceAccess.objects.filter(license=sub.license).first()
        sa.status = ServiceAccess.Status.ACTIVE
        sa.save()
        resp = admin_client.post(f"/api/v1/admin/service-accesses/{sa.id}/reprovision/")
        assert resp.status_code == 400

    def test_client_can_view_own_services(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        product, pricing = _make_product(slug="client-services", services=("chatwoot",))
        customer = _make_customer("36.000.000/0001-36")
        user = CustomUser.objects.create_user(
            username="svcuser", email="svcuser@test.com", password="pass123"
        )
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")
        sub = _make_subscription(customer, product, pricing)

        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": "svcuser@test.com", "password": "pass123"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")

        resp = client.get(f"/api/v1/client/subscriptions/{sub.id}/services/")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# License validation endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLicenseValidation:
    def test_valid_license_returns_valid_true(self, api_client):
        product, pricing = _make_product(slug="validate-valid", services=("n8n",))
        customer = _make_customer("37.000.000/0001-37")
        sub = _make_subscription(customer, product, pricing)
        key = sub.license.key

        resp = api_client.get(f"/api/v1/client/subscriptions/validate-license/?key={key}")
        assert resp.status_code == 200
        assert resp.json()["data"]["valid"] is True

    def test_invalid_key_returns_404(self, api_client):
        resp = api_client.get("/api/v1/client/subscriptions/validate-license/?key=nonexistent")
        assert resp.status_code == 404

    def test_expired_license_is_invalid(self, api_client):
        from apps.subscriptions.commands import ExpireSubscriptionCommand

        product, pricing = _make_product(slug="validate-expired", services=("n8n",))
        customer = _make_customer("38.000.000/0001-38")
        sub = _make_subscription(customer, product, pricing)
        ExpireSubscriptionCommand().execute(sub.id)
        ExpireSubscriptionCommand().execute(sub.id)  # → expired

        sub.refresh_from_db()
        resp = api_client.get(
            f"/api/v1/client/subscriptions/validate-license/?key={sub.license.key}"
        )
        assert resp.json()["data"]["valid"] is False


# ---------------------------------------------------------------------------
# Client — Reactivate subscription endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientReactivateSubscription:
    def _setup_suspended(self, doc="39.000.000/0001-39"):
        from apps.accounts.models import CustomUser
        from apps.subscriptions.commands import SuspendSubscriptionCommand

        product, pricing = _make_product(slug=f"react-{doc[:4]}", services=("n8n",))
        customer = _make_customer(doc)
        user = CustomUser.objects.create_user(
            username=doc[:6], email=f"{doc[:6]}@react.com", password="pass123"
        )
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")
        sub = _make_subscription(customer, product, pricing)

        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(sub.id)

        from rest_framework.test import APIClient

        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "pass123"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        sub.refresh_from_db()
        return client, sub

    def test_client_can_reactivate_suspended_subscription(self):
        client, sub = self._setup_suspended("39.000.000/0001-39")
        resp = client.post(f"/api/v1/client/subscriptions/{sub.id}/reactivate/")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "active"

    def test_reactivate_updates_license_to_active(self):
        from apps.subscriptions.models import License

        client, sub = self._setup_suspended("40.000.000/0001-40")
        client.post(f"/api/v1/client/subscriptions/{sub.id}/reactivate/")
        sub.license.refresh_from_db()
        assert sub.license.status == License.Status.ACTIVE

    def test_reactivate_emits_subscription_renewed_event(self):
        from shared.models import OutboxEvent

        client, sub = self._setup_suspended("41.000.000/0001-41")
        client.post(f"/api/v1/client/subscriptions/{sub.id}/reactivate/")
        assert OutboxEvent.objects.filter(
            event_type="subscription.renewed",
            payload__subscription_id=str(sub.id),
        ).exists()

    def test_cannot_reactivate_active_subscription(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        product, pricing = _make_product(slug="react-active", services=("n8n",))
        customer = _make_customer("42.000.000/0001-42")
        user = CustomUser.objects.create_user(
            username="react42", email="react42@test.com", password="pass123"
        )
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")
        sub = _make_subscription(customer, product, pricing)

        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "pass123"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        resp = client.post(f"/api/v1/client/subscriptions/{sub.id}/reactivate/")
        assert resp.status_code == 400

    def test_cannot_reactivate_other_customers_subscription(self):
        client, sub = self._setup_suspended("43.000.000/0001-43")
        product2, pricing2 = _make_product(slug="react-other", services=("n8n",))
        other_customer = _make_customer("44.000.000/0001-44")
        other_sub = _make_subscription(other_customer, product2, pricing2)
        resp = client.post(f"/api/v1/client/subscriptions/{other_sub.id}/reactivate/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Client Cancel Subscription
# ---------------------------------------------------------------------------


def _make_client_with_active_sub(doc: str):
    """Returns (api_client, subscription) with authenticated user."""
    from rest_framework.test import APIClient

    from apps.accounts.models import CustomUser

    customer = _make_customer(doc)
    user = CustomUser.objects.create_user(
        username=f"user_{doc[:4]}", email=f"user_{doc[:4]}@papermoon.com", password="pass1234"
    )
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)

    product, pricing = _make_product(slug=f"cancel-prod-{doc[:4]}", services=("n8n",))
    sub = _make_subscription(customer, product, pricing)

    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": f"user_{doc[:4]}@papermoon.com", "password": "pass1234"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
    return client, sub


@pytest.mark.django_db
class TestClientCancelSubscription:
    def test_client_can_cancel_active_subscription(self):
        client, sub = _make_client_with_active_sub("70.000.000/0001-70")
        resp = client.post(f"/api/v1/client/subscriptions/{sub.id}/cancel/")
        assert resp.status_code == 200
        sub.refresh_from_db()
        assert sub.status == Subscription.Status.CANCELLED

    def test_cancel_emits_subscription_cancelled_event(self):
        from shared.models import OutboxEvent

        client, sub = _make_client_with_active_sub("71.000.000/0001-71")
        client.post(f"/api/v1/client/subscriptions/{sub.id}/cancel/")
        assert OutboxEvent.objects.filter(event_type="subscription.cancelled").exists()

    def test_cannot_cancel_already_cancelled_subscription(self):
        from apps.subscriptions.commands import CancelSubscriptionCommand

        client, sub = _make_client_with_active_sub("72.000.000/0001-72")
        CancelSubscriptionCommand().execute(sub.id)
        resp = client.post(f"/api/v1/client/subscriptions/{sub.id}/cancel/")
        assert resp.status_code == 400

    def test_cannot_cancel_other_customers_subscription(self):
        client, _ = _make_client_with_active_sub("73.000.000/0001-73")
        product2, pricing2 = _make_product(slug="cancel-other", services=("n8n",))
        other_customer = _make_customer("74.000.000/0001-74")
        other_sub = _make_subscription(other_customer, product2, pricing2)
        resp = client.post(f"/api/v1/client/subscriptions/{other_sub.id}/cancel/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Client API Quota
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientApiQuota:
    def _setup(self, doc: str):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        customer = _make_customer(doc)
        user = CustomUser.objects.create_user(
            username=f"quota_{doc[:4]}", email=f"quota_{doc[:4]}@papermoon.com", password="pass1234"
        )
        CustomerProfile.objects.create(
            user=user, customer=customer, role=CustomerProfile.Role.OWNER
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": f"quota_{doc[:4]}@papermoon.com", "password": "pass1234"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        return client, customer

    def test_quota_returns_zero_when_no_quota_exists(self):
        client, _ = self._setup("80.000.000/0001-80")
        resp = client.get("/api/v1/client/quota/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["used_api_calls"] == 0
        assert data["max_api_calls"] == 0

    def test_quota_returns_correct_values(self):
        from django.utils import timezone

        from apps.licensing.models import LicenseQuota

        client, customer = self._setup("81.000.000/0001-81")
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=10000,
            used_api_calls=7500,
            reset_at=timezone.now(),
        )
        resp = client.get("/api/v1/client/quota/")
        data = resp.json()["data"]
        assert data["used_api_calls"] == 7500
        assert data["max_api_calls"] == 10000
        assert data["usage_pct"] == 75.0

    def test_unauthenticated_cannot_access_quota(self):
        from rest_framework.test import APIClient

        resp = APIClient().get("/api/v1/client/quota/")
        assert resp.status_code == 401
