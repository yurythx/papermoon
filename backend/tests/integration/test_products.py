"""Integration tests for the Product catalog (admin CRUD)."""

import pytest

from apps.products.models import Pricing, Product, ServiceComponent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_product(name="PaperMoon Starter", slug="starter"):
    return Product.objects.create(name=name, slug=slug, description="Test product")


def _create_pricing(product, cycle="monthly", amount="299.00"):
    return Pricing.objects.create(product=product, billing_cycle=cycle, amount=amount)


# ---------------------------------------------------------------------------
# Product CRUD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProductAdminCRUD:
    def test_admin_can_create_product(self, admin_client):
        resp = admin_client.post(
            "/api/v1/admin/products/",
            {"name": "PaperMoon Pro", "slug": "pro", "description": "Pro plan"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["slug"] == "pro"

    def test_admin_can_list_products(self, admin_client):
        _create_product()
        resp = admin_client.get("/api/v1/admin/products/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_admin_can_update_product(self, admin_client):
        product = _create_product(slug="update-me")
        resp = admin_client.patch(
            f"/api/v1/admin/products/{product.id}/",
            {"description": "Updated"},
            format="json",
        )
        assert resp.status_code == 200

    def test_admin_can_deactivate_product(self, admin_client):
        product = _create_product(slug="deactivate-me")
        resp = admin_client.delete(f"/api/v1/admin/products/{product.id}/")
        assert resp.status_code == 204
        product.refresh_from_db()
        assert product.is_active is False

    def test_non_admin_cannot_create_product(self, customer_client):
        resp = customer_client.post(
            "/api/v1/admin/products/",
            {"name": "Hack", "slug": "hack"},
            format="json",
        )
        assert resp.status_code == 403

    def test_duplicate_slug_returns_400(self, admin_client):
        _create_product(slug="unique-slug")
        resp = admin_client.post(
            "/api/v1/admin/products/",
            {"name": "Another", "slug": "unique-slug"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestServiceComponentCRUD:
    def test_admin_can_add_component(self, admin_client):
        product = _create_product(slug="comp-test")
        resp = admin_client.post(
            f"/api/v1/admin/products/{product.id}/components/",
            {"service_key": "chatwoot", "config": {}},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["service_key"] == "chatwoot"

    def test_admin_can_add_tailscale_component(self, admin_client):
        product = _create_product(slug="tailscale-comp-test")
        resp = admin_client.post(
            f"/api/v1/admin/products/{product.id}/components/",
            {"service_key": "tailscale", "config": {}},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["service_key"] == "tailscale"

    def test_admin_can_list_components(self, admin_client):
        product = _create_product(slug="comp-list")
        ServiceComponent.objects.create(product=product, service_key="n8n")
        ServiceComponent.objects.create(product=product, service_key="chatwoot")
        resp = admin_client.get(f"/api/v1/admin/products/{product.id}/components/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_invalid_service_key_rejected(self, admin_client):
        product = _create_product(slug="invalid-key")
        resp = admin_client.post(
            f"/api/v1/admin/products/{product.id}/components/",
            {"service_key": "unknown_service"},
            format="json",
        )
        assert resp.status_code == 400

    def test_duplicate_component_rejected(self, admin_client):
        product = _create_product(slug="dup-comp")
        ServiceComponent.objects.create(product=product, service_key="n8n")
        resp = admin_client.post(
            f"/api/v1/admin/products/{product.id}/components/",
            {"service_key": "n8n"},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestPricingCRUD:
    def test_admin_can_add_pricing(self, admin_client):
        product = _create_product(slug="pricing-test")
        resp = admin_client.post(
            f"/api/v1/admin/products/{product.id}/pricings/",
            {"billing_cycle": "monthly", "amount": "199.00", "trial_days": 7},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["billing_cycle"] == "monthly"
        assert data["trial_days"] == 7

    def test_admin_can_list_pricings(self, admin_client):
        product = _create_product(slug="pricing-list")
        _create_pricing(product, "monthly")
        _create_pricing(product, "annual", "1990.00")
        resp = admin_client.get(f"/api/v1/admin/products/{product.id}/pricings/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2


# ---------------------------------------------------------------------------
# Product deactivation guard
# ---------------------------------------------------------------------------


def _create_active_subscription(product):
    """Creates Customer → Pricing → active Subscription for a product."""
    import datetime

    from django.utils import timezone

    from apps.customers.models import Customer
    from apps.subscriptions.models import Subscription

    pricing = _create_pricing(product, "monthly")
    customer = Customer.objects.create(company_name="Guard Corp", document="77.777.777/0001-77")
    return Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now() + datetime.timedelta(days=30),
    )


@pytest.mark.django_db
class TestProductDeactivationGuard:
    def test_delete_product_with_active_subscription_returns_400(self, admin_client):
        product = _create_product(slug="guard-delete")
        _create_active_subscription(product)

        resp = admin_client.delete(f"/api/v1/admin/products/{product.id}/")
        assert resp.status_code == 400
        product.refresh_from_db()
        assert product.is_active is True  # not changed

    def test_patch_deactivate_product_with_active_subscription_returns_400(self, admin_client):
        product = _create_product(slug="guard-patch")
        _create_active_subscription(product)

        resp = admin_client.patch(
            f"/api/v1/admin/products/{product.id}/",
            {"is_active": False},
            format="json",
        )
        assert resp.status_code == 400
        product.refresh_from_db()
        assert product.is_active is True

    def test_delete_product_without_subscriptions_succeeds(self, admin_client):
        product = _create_product(slug="guard-no-sub")
        resp = admin_client.delete(f"/api/v1/admin/products/{product.id}/")
        assert resp.status_code == 204
        product.refresh_from_db()
        assert product.is_active is False

    def test_patch_deactivate_product_without_subscriptions_succeeds(self, admin_client):
        product = _create_product(slug="guard-patch-ok")
        resp = admin_client.patch(
            f"/api/v1/admin/products/{product.id}/",
            {"is_active": False},
            format="json",
        )
        assert resp.status_code == 200
        product.refresh_from_db()
        assert product.is_active is False

    def test_delete_product_with_cancelled_subscription_succeeds(self, admin_client):
        """Cancelled subscriptions are not active — deletion should be allowed."""
        import datetime

        from django.utils import timezone

        from apps.customers.models import Customer
        from apps.subscriptions.models import Subscription

        product = _create_product(slug="guard-cancelled")
        pricing = _create_pricing(product, "monthly", "99.00")
        customer = Customer.objects.create(
            company_name="Cancelled Corp", document="88.888.888/0001-88"
        )
        Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.CANCELLED,
            starts_at=timezone.now(),
            expires_at=timezone.now() + datetime.timedelta(days=30),
        )

        resp = admin_client.delete(f"/api/v1/admin/products/{product.id}/")
        assert resp.status_code == 204
