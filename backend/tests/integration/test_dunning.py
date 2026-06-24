"""Integration tests for apps/billing/tasks.py — process_dunning."""

import datetime
from unittest.mock import patch
from uuid import uuid4

from django.utils import timezone
import pytest

from apps.billing.models import Invoice
from apps.customers.models import Customer
from apps.products.models import Pricing, Product
from apps.subscriptions.models import License, Subscription
from shared.models import OutboxEvent


def _make_customer(n: int = 1) -> Customer:
    return Customer.objects.create(
        company_name=f"Dunning Corp {n}",
        document=f"{n:02d}.{n:03d}.{n:03d}/0001-{(n * 9) % 100:02d}",
    )


def _make_subscription(customer: Customer, days_until_expiry: int = 30) -> Subscription:
    product = Product.objects.create(name="Dunning Product", slug=f"dp-{uuid4().hex[:6]}")
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="200.00")
    expires_at = timezone.now() + datetime.timedelta(days=days_until_expiry)
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=expires_at,
    )
    License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=expires_at,
    )
    return sub


def _make_overdue_invoice(customer: Customer, days_overdue: int, subscription=None) -> Invoice:
    due_date = datetime.date.today() - datetime.timedelta(days=days_overdue)
    return Invoice.objects.create(
        customer=customer,
        subscription=subscription,
        amount="200.00",
        due_date=due_date,
        status=Invoice.Status.OVERDUE,
    )


# ---------------------------------------------------------------------------
# D+3 — email reminder
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDunningD3:
    def test_creates_dunning_d3_outbox_event(self, customer):
        _make_overdue_invoice(customer, days_overdue=4)

        from apps.billing.tasks import process_dunning

        process_dunning()

        assert OutboxEvent.objects.filter(event_type="payment.dunning_d3").count() == 1

    def test_event_payload_contains_invoice_id(self, customer):
        invoice = _make_overdue_invoice(customer, days_overdue=3)

        from apps.billing.tasks import process_dunning

        process_dunning()

        event = OutboxEvent.objects.get(event_type="payment.dunning_d3")
        assert event.payload["invoice_id"] == str(invoice.id)
        assert event.payload["customer_id"] == str(customer.id)
        assert "days_overdue" in event.payload

    def test_invoice_not_overdue_long_enough_skipped(self, customer):
        _make_overdue_invoice(customer, days_overdue=2)

        from apps.billing.tasks import process_dunning

        process_dunning()

        assert OutboxEvent.objects.filter(event_type="payment.dunning_d3").count() == 0

    def test_idempotent_does_not_duplicate_event(self, customer):
        _make_overdue_invoice(customer, days_overdue=5)

        from apps.billing.tasks import process_dunning

        process_dunning()
        process_dunning()

        assert OutboxEvent.objects.filter(event_type="payment.dunning_d3").count() == 1

    def test_outbox_create_failure_logged_and_other_invoices_still_processed(self, customer):
        other_customer = Customer.objects.create(
            company_name="Dunning Corp 2", document="02.002.002/0001-18"
        )
        invoice_a = _make_overdue_invoice(customer, days_overdue=4)
        invoice_b = _make_overdue_invoice(other_customer, days_overdue=4)

        from apps.billing.tasks import process_dunning

        original_create = OutboxEvent.objects.create

        def _flaky_create(*args, **kwargs):
            if kwargs.get("payload", {}).get("invoice_id") == str(invoice_a.id):
                raise RuntimeError("db unavailable")
            return original_create(*args, **kwargs)

        with patch("shared.models.OutboxEvent.objects.create", side_effect=_flaky_create):
            process_dunning()

        assert not OutboxEvent.objects.filter(
            event_type="payment.dunning_d3", payload__invoice_id=str(invoice_a.id)
        ).exists()
        assert OutboxEvent.objects.filter(
            event_type="payment.dunning_d3", payload__invoice_id=str(invoice_b.id)
        ).exists()

    def test_paid_invoice_not_targeted(self, customer):
        invoice = _make_overdue_invoice(customer, days_overdue=4)
        invoice.status = Invoice.Status.PAID
        invoice.save()

        from apps.billing.tasks import process_dunning

        process_dunning()

        assert OutboxEvent.objects.filter(event_type="payment.dunning_d3").count() == 0


# ---------------------------------------------------------------------------
# D+7 — subscription suspension
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDunningD7:
    def test_suspends_linked_subscription_at_d7(self, customer):
        sub = _make_subscription(customer)
        _make_overdue_invoice(customer, days_overdue=8, subscription=sub)

        from apps.billing.tasks import process_dunning

        with patch("apps.provisioning.handlers.get_provisioner", side_effect=Exception("no-op")):
            process_dunning()

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.SUSPENDED

    def test_invoice_without_subscription_not_suspended(self, customer):
        _make_overdue_invoice(customer, days_overdue=8, subscription=None)

        from apps.billing.tasks import process_dunning

        process_dunning()

        assert not Subscription.objects.exists()

    def test_d7_invoice_also_emits_d3_event(self, customer):
        sub = _make_subscription(customer)
        _make_overdue_invoice(customer, days_overdue=8, subscription=sub)

        from apps.billing.tasks import process_dunning

        with patch("apps.provisioning.handlers.get_provisioner", side_effect=Exception("no-op")):
            process_dunning()

        assert OutboxEvent.objects.filter(event_type="payment.dunning_d3").exists()

    def test_already_suspended_subscription_is_idempotent(self, customer):
        sub = _make_subscription(customer)
        sub.status = Subscription.Status.SUSPENDED
        sub.save()
        _make_overdue_invoice(customer, days_overdue=8, subscription=sub)

        from apps.billing.tasks import process_dunning

        process_dunning()

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.SUSPENDED
