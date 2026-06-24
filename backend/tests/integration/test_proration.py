"""Integration tests for proration in ChangeSubscriptionPlanCommand."""

import datetime
import decimal
from unittest.mock import patch
from uuid import uuid4

from django.utils import timezone
import pytest

from apps.billing.models import Invoice
from apps.customers.models import Customer
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.models import License, Subscription


def _make_product(monthly_price: str = "100.00", annual_price: str = "900.00"):
    """Creates a product with monthly (cheap) and annual (expensive) pricings."""
    slug = f"proration-{uuid4().hex[:6]}"
    product = Product.objects.create(name=f"Product {slug}", slug=slug)
    ServiceComponent.objects.create(product=product, service_key="n8n")
    monthly = Pricing.objects.create(product=product, billing_cycle="monthly", amount=monthly_price)
    annual = Pricing.objects.create(product=product, billing_cycle="annual", amount=annual_price)
    return product, monthly, annual


def _make_customer() -> Customer:
    uid = uuid4().hex[:6]
    return Customer.objects.create(
        company_name=f"Proration Corp {uid}",
        document="11.222.333/0001-81",
    )


def _make_subscription(
    customer: Customer, product: Product, pricing: Pricing, days_remaining: int = 15
) -> Subscription:
    now = timezone.now()
    expires_at = now + datetime.timedelta(days=days_remaining)
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=now,
        expires_at=expires_at,
    )
    License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=now,
        valid_until=expires_at,
    )
    return sub


@pytest.mark.django_db
class TestProration:
    def _upgrade(self, sub: Subscription, new_pricing: Pricing) -> Subscription:
        from apps.subscriptions.commands import ChangeSubscriptionPlanCommand

        with (
            patch("apps.support.client.ChatwootClient"),
            patch("apps.provisioning.n8n.N8nProvisioner.provision", return_value="ext_stub"),
        ):
            return ChangeSubscriptionPlanCommand().execute(
                subscription_id=sub.id,
                new_pricing_id=new_pricing.id,
            )

    def test_upgrade_creates_proration_invoice(self, db):
        customer = _make_customer()
        product, monthly, annual = _make_product("100.00", "900.00")
        # Upgrade from monthly (R$100) to annual (R$900) with 15 days remaining
        sub = _make_subscription(customer, product, monthly, days_remaining=15)

        self._upgrade(sub, annual)

        proration_invoices = Invoice.objects.filter(
            customer=customer,
            invoice_type=Invoice.Type.SUBSCRIPTION,
        )
        assert proration_invoices.exists(), "Proration invoice should be created on upgrade"

    def test_proration_amount_is_positive(self, db):
        customer = _make_customer()
        product, monthly, annual = _make_product("100.00", "900.00")
        sub = _make_subscription(customer, product, monthly, days_remaining=15)

        self._upgrade(sub, annual)

        inv = Invoice.objects.filter(
            customer=customer, invoice_type=Invoice.Type.SUBSCRIPTION
        ).first()
        assert inv is not None
        assert inv.amount > decimal.Decimal("0"), "Proration amount must be positive on upgrade"

    def test_proration_amount_is_proportional(self, db):
        customer = _make_customer()
        # monthly=100, annual=400 — big enough difference for 15/30 days to matter
        product, monthly, annual = _make_product("100.00", "400.00")
        sub = _make_subscription(customer, product, monthly, days_remaining=15)

        self._upgrade(sub, annual)

        inv = Invoice.objects.filter(
            customer=customer, invoice_type=Invoice.Type.SUBSCRIPTION
        ).first()
        assert inv is not None
        # old cycle = monthly = 30 days; (400 - 100) * 15/30 = 150; allow ±5
        assert abs(float(inv.amount) - 150.0) < 5, f"Expected ~150, got {inv.amount}"

    def test_downgrade_does_not_create_proration_invoice(self, db):
        customer = _make_customer()
        product, monthly, annual = _make_product("100.00", "900.00")
        # Start with annual (expensive), downgrade to monthly (cheap)
        sub = _make_subscription(customer, product, annual, days_remaining=15)

        self._upgrade(sub, monthly)

        proration_invoices = Invoice.objects.filter(
            customer=customer,
            invoice_type=Invoice.Type.SUBSCRIPTION,
        )
        assert not proration_invoices.exists(), "Downgrade should not create a proration invoice"

    def test_proration_invoice_has_due_date_plus_3(self, db):
        customer = _make_customer()
        product, monthly, annual = _make_product("100.00", "900.00")
        sub = _make_subscription(customer, product, monthly, days_remaining=15)

        self._upgrade(sub, annual)

        inv = Invoice.objects.filter(
            customer=customer, invoice_type=Invoice.Type.SUBSCRIPTION
        ).first()
        assert inv is not None
        expected_due = datetime.date.today() + datetime.timedelta(days=3)
        assert inv.due_date == expected_due

    def test_proration_emits_renewal_invoice_outbox_event(self, db):
        from shared.models import OutboxEvent

        customer = _make_customer()
        product, monthly, annual = _make_product("100.00", "900.00")
        sub = _make_subscription(customer, product, monthly, days_remaining=15)

        self._upgrade(sub, annual)

        assert OutboxEvent.objects.filter(event_type="renewal_invoice.created").exists()

    def test_same_pricing_raises_error(self, db):
        customer = _make_customer()
        product, monthly, _ = _make_product()
        sub = _make_subscription(customer, product, monthly, days_remaining=15)

        from apps.subscriptions.commands import ChangeSubscriptionPlanCommand

        with pytest.raises(ValueError, match="same"):
            ChangeSubscriptionPlanCommand().execute(
                subscription_id=sub.id,
                new_pricing_id=monthly.id,
            )

    def test_one_time_plan_skips_proration(self, db):
        customer = _make_customer()
        slug = f"ot-{uuid4().hex[:6]}"
        product = Product.objects.create(name="OT Product", slug=slug)
        ServiceComponent.objects.create(product=product, service_key="n8n")
        one_time = Pricing.objects.create(product=product, billing_cycle="one_time", amount="50.00")
        lifetime = Pricing.objects.create(
            product=product, billing_cycle="lifetime", amount="500.00"
        )
        sub = _make_subscription(customer, product, one_time, days_remaining=15)

        self._upgrade(sub, lifetime)

        # One-time and lifetime plans don't pro-rate
        assert not Invoice.objects.filter(
            customer=customer, invoice_type=Invoice.Type.SUBSCRIPTION
        ).exists()
