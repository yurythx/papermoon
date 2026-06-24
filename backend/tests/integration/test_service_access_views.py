"""Integration tests for apps/subscriptions/views_service_access.py."""

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.customers.models import Customer, CustomerProfile
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.models import License, ServiceAccess, Subscription


def _make_customer_with_owner(email: str, doc: str):
    user = CustomUser.objects.create_user(
        username=email.split("@")[0], email=email, password="pass123"
    )
    customer = Customer.objects.create(company_name="SA Test Co", document=doc)
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)
    return customer, user


def _auth(client: APIClient, email: str, password="pass123") -> APIClient:
    resp = client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
    return client


def _make_subscription_with_service(customer: Customer, service_key: str = "n8n"):
    import datetime
    import uuid

    from django.utils import timezone

    product = Product.objects.create(name="SA Product", slug=f"sap-{uuid.uuid4().hex[:6]}")
    ServiceComponent.objects.create(product=product, service_key=service_key)
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now() + datetime.timedelta(days=30),
    )
    license_obj = License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + datetime.timedelta(days=30),
    )
    sa = ServiceAccess.objects.create(
        license=license_obj,
        service_key=service_key,
        status=ServiceAccess.Status.ACTIVE,
    )
    return sub, license_obj, sa


# ---------------------------------------------------------------------------
# Admin — list/create service accesses
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminServiceAccessListCreate:
    BASE = "/api/v1/admin/subscriptions/{}/services/"

    def test_missing_service_key_returns_400(self, admin_client, customer):
        sub, _, _ = _make_subscription_with_service(customer)
        resp = admin_client.post(self.BASE.format(sub.id), {}, format="json")
        assert resp.status_code == 400
        assert "service_key" in str(resp.json())

    def test_invalid_service_key_returns_400(self, admin_client, customer):
        sub, _, _ = _make_subscription_with_service(customer)
        resp = admin_client.post(
            self.BASE.format(sub.id), {"service_key": "invalid_service_xyz"}, format="json"
        )
        assert resp.status_code == 400

    def test_duplicate_service_key_returns_400(self, admin_client, customer):
        sub, _, _ = _make_subscription_with_service(customer, service_key="n8n")
        resp = admin_client.post(self.BASE.format(sub.id), {"service_key": "n8n"}, format="json")
        assert resp.status_code == 400

    def test_list_returns_service_accesses(self, admin_client, customer):
        sub, _, sa = _make_subscription_with_service(customer)
        resp = admin_client.get(self.BASE.format(sub.id))
        assert resp.status_code == 200
        keys = [item["service_key"] for item in resp.json()["data"]]
        assert "n8n" in keys


# ---------------------------------------------------------------------------
# Admin — detail / patch / delete
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminServiceAccessDetail:
    BASE = "/api/v1/admin/service-accesses/{}/"

    def test_get_returns_service_access(self, admin_client, customer):
        _, _, sa = _make_subscription_with_service(customer)
        resp = admin_client.get(self.BASE.format(sa.id))
        assert resp.status_code == 200
        assert resp.json()["data"]["service_key"] == "n8n"

    def test_get_404_for_unknown_id(self, admin_client):
        import uuid

        resp = admin_client.get(self.BASE.format(uuid.uuid4()))
        assert resp.status_code == 404

    def test_patch_updates_config(self, admin_client, customer):
        _, _, sa = _make_subscription_with_service(customer)
        resp = admin_client.patch(
            self.BASE.format(sa.id),
            {"config": {"key": "value"}},
            format="json",
        )
        assert resp.status_code == 200
        sa.refresh_from_db()
        assert sa.config == {"key": "value"}

    def test_patch_updates_external_id(self, admin_client, customer):
        _, _, sa = _make_subscription_with_service(customer)
        resp = admin_client.patch(
            self.BASE.format(sa.id),
            {"external_id": "ext-123"},
            format="json",
        )
        assert resp.status_code == 200
        sa.refresh_from_db()
        assert sa.external_id == "ext-123"

    def test_delete_marks_deprovisioned_and_emits_outbox_event(self, admin_client, customer):
        from shared.models import OutboxEvent

        _, _, sa = _make_subscription_with_service(customer)
        resp = admin_client.delete(self.BASE.format(sa.id))
        assert resp.status_code == 204
        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.DEPROVISIONED
        assert OutboxEvent.objects.filter(event_type="service_access.deprovision").exists()


# ---------------------------------------------------------------------------
# Admin — reprovision
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminServiceAccessReprovision:
    BASE = "/api/v1/admin/service-accesses/{}/reprovision/"

    def test_reprovision_failed_service_emits_outbox_event(self, admin_client, customer):
        from shared.models import OutboxEvent

        _, _, sa = _make_subscription_with_service(customer)
        sa.status = ServiceAccess.Status.FAILED
        sa.error = "provisioning error"
        sa.save()

        resp = admin_client.post(self.BASE.format(sa.id), {}, format="json")
        assert resp.status_code == 200
        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.PROVISIONING
        assert sa.error is None
        assert OutboxEvent.objects.filter(event_type="service_access.provision").exists()

    def test_reprovision_active_service_returns_400(self, admin_client, customer):
        _, _, sa = _make_subscription_with_service(customer)
        resp = admin_client.post(self.BASE.format(sa.id), {}, format="json")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Client — list service accesses (own subscriptions only)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientServiceAccessList:
    def test_client_can_list_own_service_accesses(self, customer_client, customer_with_profile):
        sub, _, sa = _make_subscription_with_service(customer_with_profile)
        resp = customer_client.get(f"/api/v1/client/subscriptions/{sub.id}/services/")
        assert resp.status_code == 200
        keys = [item["service_key"] for item in resp.json()["data"]]
        assert "n8n" in keys

    def test_client_without_profile_gets_403(self, api_client, regular_user):
        import uuid

        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.get(f"/api/v1/client/subscriptions/{uuid.uuid4()}/services/")
        assert resp.status_code in (403, 404)
