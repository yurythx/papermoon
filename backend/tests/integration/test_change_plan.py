"""Integration tests for the change-plan endpoint (admin and client)."""

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.customers.models import Customer, CustomerProfile
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.models import ServiceAccess, Subscription

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_product(slug: str):
    product = Product.objects.create(name=f"Product {slug}", slug=slug)
    ServiceComponent.objects.create(product=product, service_key="n8n")
    base_pricing = Pricing.objects.create(
        product=product,
        billing_cycle="monthly",
        amount="199.00",
        max_api_calls=5000,
        max_users=3,
    )
    premium_pricing = Pricing.objects.create(
        product=product,
        billing_cycle="annual",
        amount="1990.00",
        max_api_calls=100000,
        max_users=50,
    )
    return product, base_pricing, premium_pricing


def _make_customer(doc: str) -> Customer:
    return Customer.objects.create(company_name="Change Plan Corp", document=doc)


def _make_subscription(customer: Customer, product: Product, pricing: Pricing) -> Subscription:
    from apps.subscriptions.commands import CreateSubscriptionCommand

    with (
        patch("apps.support.client.ChatwootClient"),
        patch("apps.provisioning.n8n.N8nProvisioner.provision", return_value="ext_stub"),
    ):
        return CreateSubscriptionCommand().execute(
            customer_id=customer.id,
            product_id=product.id,
            pricing_id=pricing.id,
        )


def _client_for_customer(customer: Customer, email: str, password: str = "pass123") -> APIClient:
    user = CustomUser.objects.create_user(
        username=email.split("@")[0], email=email, password=password
    )
    CustomerProfile.objects.create(user=user, customer=customer, role="owner")
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
    return client


# ---------------------------------------------------------------------------
# Admin change-plan
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminChangePlan:
    def test_admin_can_upgrade_subscription(self, admin_client):
        product, base_pricing, premium_pricing = _make_product("admin-upgrade")
        customer = _make_customer("40.000.000/0001-40")
        sub = _make_subscription(customer, product, base_pricing)

        resp = admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )

        assert resp.status_code == 201
        new_id = resp.json()["data"]["id"]
        assert new_id != str(sub.id)
        assert resp.json()["data"]["status"] == "active"

    def test_old_subscription_is_cancelled_after_upgrade(self, admin_client):
        product, base_pricing, premium_pricing = _make_product("admin-old-cancel")
        customer = _make_customer("41.000.000/0001-41")
        sub = _make_subscription(customer, product, base_pricing)

        admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.CANCELLED

    def test_new_subscription_has_new_pricing(self, admin_client):
        product, base_pricing, premium_pricing = _make_product("admin-pricing-check")
        customer = _make_customer("42.000.000/0001-42")
        sub = _make_subscription(customer, product, base_pricing)

        resp = admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )

        new_sub = Subscription.objects.get(pk=resp.json()["data"]["id"])
        assert new_sub.pricing_id == premium_pricing.id

    def test_service_accesses_are_carried_over(self, admin_client):
        product, base_pricing, premium_pricing = _make_product("admin-carry-sa")
        customer = _make_customer("43.000.000/0001-43")
        sub = _make_subscription(customer, product, base_pricing)
        # Simulate provisioned state
        sub.license.service_accesses.update(
            status=ServiceAccess.Status.ACTIVE, external_id="ext_carried"
        )

        resp = admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )

        new_sub = Subscription.objects.get(pk=resp.json()["data"]["id"])
        sa = new_sub.license.service_accesses.get(service_key="n8n")
        assert sa.external_id == "ext_carried"

    def test_same_pricing_returns_400(self, admin_client):
        product, base_pricing, _ = _make_product("admin-same-plan")
        customer = _make_customer("44.000.000/0001-44")
        sub = _make_subscription(customer, product, base_pricing)

        resp = admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(base_pricing.id)},
            format="json",
        )

        assert resp.status_code == 400

    def test_missing_pricing_id_returns_400(self, admin_client):
        product, base_pricing, _ = _make_product("admin-missing-id")
        customer = _make_customer("45.000.000/0001-45")
        sub = _make_subscription(customer, product, base_pricing)

        resp = admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {},
            format="json",
        )

        assert resp.status_code == 400

    def test_emits_plan_changed_outbox_event(self, admin_client):
        from shared.models import OutboxEvent

        product, base_pricing, premium_pricing = _make_product("admin-outbox")
        customer = _make_customer("46.000.000/0001-46")
        sub = _make_subscription(customer, product, base_pricing)

        admin_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )

        assert OutboxEvent.objects.filter(event_type="subscription.plan_changed").exists()

    def test_non_admin_cannot_use_admin_change_plan(self, customer_client):
        product, base_pricing, premium_pricing = _make_product("non-admin-change")
        customer = _make_customer("47.000.000/0001-47")
        sub = _make_subscription(customer, product, base_pricing)

        resp = customer_client.post(
            f"/api/v1/admin/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Client self-service change-plan
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientChangePlan:
    def _setup(self, doc: str):
        product, base_pricing, premium_pricing = _make_product(f"client-cp-{doc[:4]}")
        customer = _make_customer(doc)
        sub = _make_subscription(customer, product, base_pricing)
        client = _client_for_customer(customer, f"user_{doc[:4]}@test.com")
        return client, sub, base_pricing, premium_pricing

    def test_client_can_change_plan(self):
        client, sub, _, premium_pricing = self._setup("48.000.000/0001-48")
        resp = client.post(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["status"] == "active"

    def test_client_cannot_change_another_customers_plan(self):
        client, _, _, _ = self._setup("49.000.000/0001-49")
        product, other_base, other_premium = _make_product("other-plan-target")
        other_customer = _make_customer("50.000.000/0001-50")
        other_sub = _make_subscription(other_customer, product, other_base)

        resp = client.post(
            f"/api/v1/client/subscriptions/{other_sub.id}/change-plan/",
            {"pricing_id": str(other_premium.id)},
            format="json",
        )

        assert resp.status_code == 404

    def test_client_same_pricing_returns_400(self):
        client, sub, base_pricing, _ = self._setup("51.000.000/0001-51")
        resp = client.post(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(base_pricing.id)},
            format="json",
        )
        assert resp.status_code == 400

    def test_unauthenticated_cannot_change_plan(self, api_client):
        product, base_pricing, premium_pricing = _make_product("unauth-change")
        customer = _make_customer("52.000.000/0001-52")
        sub = _make_subscription(customer, product, base_pricing)

        resp = api_client.post(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan/",
            {"pricing_id": str(premium_pricing.id)},
            format="json",
        )

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Change-plan preview endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestChangePlanPreview:
    def _setup(self, doc: str):
        product, base_pricing, premium_pricing = _make_product(f"preview-{doc[:4]}")
        customer = _make_customer(doc)
        sub = _make_subscription(customer, product, base_pricing)
        client = _client_for_customer(customer, f"prev_{doc[:4]}@test.com")
        return client, sub, base_pricing, premium_pricing

    def test_preview_returns_proration_for_upgrade(self):
        client, sub, _, premium = self._setup("60.000.000/0001-60")
        resp = client.get(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan-preview/",
            {"pricing_id": str(premium.id)},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "proration_amount" in data
        assert "has_proration" in data

    def test_preview_has_proration_true_for_upgrade(self):
        client, sub, _, premium = self._setup("61.000.000/0001-61")
        resp = client.get(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan-preview/",
            {"pricing_id": str(premium.id)},
        )
        data = resp.json()["data"]
        assert data["has_proration"] is True

    def test_preview_no_proration_for_downgrade(self):
        client, sub, base, premium = self._setup("62.000.000/0001-62")
        # first upgrade to premium, then preview downgrade back
        from unittest.mock import patch as _patch

        with (
            _patch("apps.support.client.ChatwootClient"),
            _patch("apps.provisioning.n8n.N8nProvisioner.provision", return_value="x"),
        ):
            from apps.subscriptions.commands import ChangeSubscriptionPlanCommand

            new_sub = ChangeSubscriptionPlanCommand().execute(sub.id, premium.id)

        resp = client.get(
            f"/api/v1/client/subscriptions/{new_sub.id}/change-plan-preview/",
            {"pricing_id": str(base.id)},
        )
        data = resp.json()["data"]
        assert data["has_proration"] is False
        assert data["proration_amount"] == "0"

    def test_preview_missing_pricing_id_returns_400(self):
        client, sub, _, _ = self._setup("63.000.000/0001-63")
        resp = client.get(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan-preview/",
        )
        assert resp.status_code == 400

    def test_preview_wrong_product_pricing_returns_400(self):
        from uuid import uuid4

        client, sub, _, _ = self._setup("64.000.000/0001-64")
        resp = client.get(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan-preview/",
            {"pricing_id": str(uuid4())},
        )
        assert resp.status_code == 400

    def test_preview_requires_authentication(self, api_client):
        product, base_pricing, premium_pricing = _make_product("preview-unauth")
        customer = _make_customer("65.000.000/0001-65")
        sub = _make_subscription(customer, product, base_pricing)

        resp = api_client.get(
            f"/api/v1/client/subscriptions/{sub.id}/change-plan-preview/",
            {"pricing_id": str(premium_pricing.id)},
        )
        assert resp.status_code == 401

    def test_preview_cannot_access_other_customers_subscription(self):
        client, _, _, _ = self._setup("66.000.000/0001-66")
        product, other_base, other_premium = _make_product("preview-isolation")
        other_customer = _make_customer("67.000.000/0001-67")
        other_sub = _make_subscription(other_customer, product, other_base)

        resp = client.get(
            f"/api/v1/client/subscriptions/{other_sub.id}/change-plan-preview/",
            {"pricing_id": str(other_premium.id)},
        )
        assert resp.status_code == 404
