"""
Unit tests for subscription lifecycle commands.
Uses real DB (django_db) since commands are tightly coupled to ORM transactions.
External HTTP calls (Asaas, Chatwoot) are patched out.
"""

from unittest.mock import patch
from uuid import uuid4

import pytest

from apps.customers.models import Customer
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.commands import (
    CancelSubscriptionCommand,
    ChangeSubscriptionPlanCommand,
    CreateSubscriptionCommand,
    ExpireSubscriptionCommand,
    ReactivateSubscriptionCommand,
    RenewSubscriptionCommand,
    SuspendSubscriptionCommand,
)
from apps.subscriptions.models import License, ServiceAccess, Subscription
from shared.models import OutboxEvent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def product_with_pricing(db):
    product = Product.objects.create(name="Unit Test Product", slug=f"unit-{uuid4().hex[:6]}")
    ServiceComponent.objects.create(product=product, service_key="n8n")
    pricing = Pricing.objects.create(
        product=product,
        billing_cycle="monthly",
        amount="199.00",
        max_api_calls=5000,
        max_users=3,
    )
    return product, pricing


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        company_name="Unit Corp", document=f"{uuid4().int % 10**14:014d}"[:18]
    )


@pytest.fixture
def subscription(db, product_with_pricing, customer):
    product, pricing = product_with_pricing
    with patch("apps.support.client.ChatwootClient"):
        return CreateSubscriptionCommand().execute(
            customer_id=customer.id,
            product_id=product.id,
            pricing_id=pricing.id,
        )


# ---------------------------------------------------------------------------
# CreateSubscriptionCommand
# ---------------------------------------------------------------------------


class TestCreateSubscriptionCommand:
    def test_creates_subscription_with_active_status(self, subscription):
        assert subscription.status == Subscription.Status.ACTIVE

    def test_creates_one_license(self, subscription):
        assert License.objects.filter(subscription=subscription).count() == 1

    def test_license_key_is_non_empty(self, subscription):
        assert len(subscription.license.key) >= 32

    def test_creates_service_accesses_for_each_component(self, subscription):
        accesses = ServiceAccess.objects.filter(license=subscription.license)
        assert accesses.count() == 1  # only n8n
        assert accesses.first().service_key == "n8n"
        assert accesses.first().status == ServiceAccess.Status.PROVISIONING

    def test_emits_subscription_created_outbox_event(self, subscription):
        assert OutboxEvent.objects.filter(
            event_type="subscription.created",
            payload__subscription_id=str(subscription.id),
        ).exists()

    def test_trial_pricing_creates_trial_subscription(self, db, customer):
        product = Product.objects.create(name="Trial Prod", slug=f"trial-{uuid4().hex[:6]}")
        ServiceComponent.objects.create(product=product, service_key="n8n")
        trial_pricing = Pricing.objects.create(
            product=product, billing_cycle="monthly", amount="0.00", trial_days=7
        )
        with patch("apps.support.client.ChatwootClient"):
            sub = CreateSubscriptionCommand().execute(
                customer_id=customer.id,
                product_id=product.id,
                pricing_id=trial_pricing.id,
            )
        assert sub.status == Subscription.Status.TRIAL

    def test_expires_at_is_30_days_ahead_for_monthly(self, subscription):
        delta = subscription.expires_at - subscription.starts_at
        assert 29 <= delta.days <= 31

    def test_expires_at_is_365_days_ahead_for_annual(self, db, customer):
        product = Product.objects.create(name="Annual Prod", slug=f"annual-{uuid4().hex[:6]}")
        ServiceComponent.objects.create(product=product, service_key="n8n")
        annual_pricing = Pricing.objects.create(
            product=product, billing_cycle="annual", amount="1990.00"
        )
        with patch("apps.support.client.ChatwootClient"):
            sub = CreateSubscriptionCommand().execute(
                customer_id=customer.id,
                product_id=product.id,
                pricing_id=annual_pricing.id,
            )
        delta = sub.expires_at - sub.starts_at
        assert 364 <= delta.days <= 366


# ---------------------------------------------------------------------------
# SuspendSubscriptionCommand
# ---------------------------------------------------------------------------


class TestSuspendSubscriptionCommand:
    def test_changes_status_to_suspended(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(subscription.id)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.SUSPENDED

    def test_suspends_license(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(subscription.id)
        subscription.license.refresh_from_db()
        assert subscription.license.status == License.Status.SUSPENDED

    def test_suspends_active_service_accesses(self, subscription):
        subscription.license.service_accesses.update(status=ServiceAccess.Status.ACTIVE)
        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(subscription.id)
        assert subscription.license.service_accesses.filter(
            status=ServiceAccess.Status.SUSPENDED
        ).exists()

    def test_emits_subscription_suspended_outbox_event(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(subscription.id)
        assert OutboxEvent.objects.filter(event_type="subscription.suspended").exists()

    def test_cannot_suspend_already_cancelled(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            CancelSubscriptionCommand().execute(subscription.id)
        with pytest.raises(ValueError, match="Invalid transition"):
            SuspendSubscriptionCommand().execute(subscription.id)


# ---------------------------------------------------------------------------
# ReactivateSubscriptionCommand
# ---------------------------------------------------------------------------


class TestReactivateSubscriptionCommand:
    @pytest.fixture
    def suspended_subscription(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(subscription.id)
        subscription.refresh_from_db()
        return subscription

    def test_changes_status_to_active(self, suspended_subscription):
        ReactivateSubscriptionCommand().execute(suspended_subscription.id)
        suspended_subscription.refresh_from_db()
        assert suspended_subscription.status == Subscription.Status.ACTIVE

    def test_reactivates_license(self, suspended_subscription):
        ReactivateSubscriptionCommand().execute(suspended_subscription.id)
        suspended_subscription.license.refresh_from_db()
        assert suspended_subscription.license.status == License.Status.ACTIVE

    def test_reactivates_suspended_service_accesses(self, subscription):
        # Force accesses to SUSPENDED (suspend only touches ACTIVE accesses)
        subscription.license.service_accesses.update(status=ServiceAccess.Status.SUSPENDED)
        subscription.status = Subscription.Status.SUSPENDED
        subscription.save(update_fields=["status", "updated_at"])
        subscription.license.status = License.Status.SUSPENDED
        subscription.license.save(update_fields=["status"])

        ReactivateSubscriptionCommand().execute(subscription.id)
        assert subscription.license.service_accesses.filter(
            status=ServiceAccess.Status.ACTIVE
        ).exists()

    def test_does_not_extend_expires_at(self, suspended_subscription):
        original_expiry = suspended_subscription.expires_at
        ReactivateSubscriptionCommand().execute(suspended_subscription.id)
        suspended_subscription.refresh_from_db()
        assert suspended_subscription.expires_at == original_expiry

    def test_emits_subscription_renewed_outbox_event(self, suspended_subscription):
        ReactivateSubscriptionCommand().execute(suspended_subscription.id)
        assert OutboxEvent.objects.filter(
            event_type="subscription.renewed",
            payload__subscription_id=str(suspended_subscription.id),
        ).exists()

    def test_raises_if_not_suspended(self, subscription):
        with pytest.raises(ValueError, match="Only suspended"):
            ReactivateSubscriptionCommand().execute(subscription.id)

    def test_raises_if_cancelled(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            CancelSubscriptionCommand().execute(subscription.id)
        with pytest.raises(ValueError, match="Only suspended"):
            ReactivateSubscriptionCommand().execute(subscription.id)


# ---------------------------------------------------------------------------
# RenewSubscriptionCommand
# ---------------------------------------------------------------------------


class TestRenewSubscriptionCommand:
    def test_extends_expires_at(self, subscription):
        original = subscription.expires_at
        RenewSubscriptionCommand().execute(subscription.id)
        subscription.refresh_from_db()
        assert subscription.expires_at > original

    def test_sets_status_to_active(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            SuspendSubscriptionCommand().execute(subscription.id)
        RenewSubscriptionCommand().execute(subscription.id)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.ACTIVE

    def test_reactivates_suspended_service_accesses(self, subscription):
        subscription.license.service_accesses.update(status=ServiceAccess.Status.SUSPENDED)
        RenewSubscriptionCommand().execute(subscription.id)
        assert (
            subscription.license.service_accesses.filter(status=ServiceAccess.Status.ACTIVE).count()
            == 1
        )

    def test_emits_subscription_renewed_outbox_event(self, subscription):
        RenewSubscriptionCommand().execute(subscription.id)
        assert OutboxEvent.objects.filter(event_type="subscription.renewed").exists()


# ---------------------------------------------------------------------------
# ExpireSubscriptionCommand (state machine)
# ---------------------------------------------------------------------------


class TestExpireSubscriptionCommand:
    def test_active_transitions_to_grace_period(self, subscription):
        ExpireSubscriptionCommand().execute(subscription.id)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.GRACE_PERIOD

    def test_grace_period_transitions_to_expired(self, subscription):
        ExpireSubscriptionCommand().execute(subscription.id)
        ExpireSubscriptionCommand().execute(subscription.id)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.EXPIRED

    def test_expired_license_has_expired_status(self, subscription):
        ExpireSubscriptionCommand().execute(subscription.id)
        ExpireSubscriptionCommand().execute(subscription.id)
        subscription.license.refresh_from_db()
        assert subscription.license.status == License.Status.EXPIRED

    def test_service_accesses_deprovisioned_on_expiry(self, subscription):
        subscription.license.service_accesses.update(status=ServiceAccess.Status.ACTIVE)
        ExpireSubscriptionCommand().execute(subscription.id)  # → grace
        ExpireSubscriptionCommand().execute(subscription.id)  # → expired
        assert subscription.license.service_accesses.filter(
            status=ServiceAccess.Status.DEPROVISIONED
        ).exists()

    def test_emits_grace_period_event_on_first_expire(self, subscription):
        ExpireSubscriptionCommand().execute(subscription.id)
        assert OutboxEvent.objects.filter(event_type="subscription.grace_period").exists()

    def test_emits_expired_event_on_second_expire(self, subscription):
        ExpireSubscriptionCommand().execute(subscription.id)
        ExpireSubscriptionCommand().execute(subscription.id)
        assert OutboxEvent.objects.filter(event_type="subscription.expired").exists()

    def test_cannot_expire_cancelled_subscription(self, subscription):
        with patch("apps.support.client.ChatwootClient"):
            CancelSubscriptionCommand().execute(subscription.id)
        with pytest.raises(ValueError, match="Invalid transition"):
            ExpireSubscriptionCommand().execute(subscription.id)


# ---------------------------------------------------------------------------
# ChangeSubscriptionPlanCommand (upgrade/downgrade)
# ---------------------------------------------------------------------------


class TestChangeSubscriptionPlanCommand:
    @pytest.fixture
    def premium_pricing(self, product_with_pricing):
        product, _ = product_with_pricing
        return Pricing.objects.create(
            product=product,
            billing_cycle="annual",
            amount="1990.00",
            max_api_calls=100000,
            max_users=50,
        )

    def test_creates_new_subscription_with_new_pricing(self, subscription, premium_pricing):
        new_sub = ChangeSubscriptionPlanCommand().execute(subscription.id, premium_pricing.id)
        assert new_sub.pricing_id == premium_pricing.id
        assert new_sub.status == Subscription.Status.ACTIVE

    def test_cancels_old_subscription(self, subscription, premium_pricing):
        ChangeSubscriptionPlanCommand().execute(subscription.id, premium_pricing.id)
        subscription.refresh_from_db()
        assert subscription.status == Subscription.Status.CANCELLED

    def test_carries_over_service_accesses(self, subscription, premium_pricing):
        subscription.license.service_accesses.update(
            status=ServiceAccess.Status.ACTIVE, external_id="ext_123"
        )
        new_sub = ChangeSubscriptionPlanCommand().execute(subscription.id, premium_pricing.id)
        new_accesses = new_sub.license.service_accesses.all()
        assert new_accesses.count() == 1
        assert new_accesses.first().external_id == "ext_123"

    def test_raises_if_same_pricing(self, subscription, product_with_pricing):
        _, same_pricing = product_with_pricing
        with pytest.raises(ValueError, match="same as the current one"):
            ChangeSubscriptionPlanCommand().execute(subscription.id, same_pricing.id)

    def test_new_license_key_is_different(self, subscription, premium_pricing):
        old_key = subscription.license.key
        new_sub = ChangeSubscriptionPlanCommand().execute(subscription.id, premium_pricing.id)
        assert new_sub.license.key != old_key

    def test_emits_plan_changed_and_created_events(self, subscription, premium_pricing):
        ChangeSubscriptionPlanCommand().execute(subscription.id, premium_pricing.id)
        assert OutboxEvent.objects.filter(event_type="subscription.plan_changed").exists()
        assert OutboxEvent.objects.filter(event_type="subscription.created").count() >= 1


# ---------------------------------------------------------------------------
# GenerateRenewalInvoiceCommand
# ---------------------------------------------------------------------------


class TestGenerateRenewalInvoiceCommand:
    def test_creates_invoice_linked_to_subscription(self, subscription, db):
        from apps.billing.models import Invoice
        from apps.subscriptions.renewal import GenerateRenewalInvoiceCommand

        invoice = GenerateRenewalInvoiceCommand().execute(subscription.id)
        assert invoice is not None
        assert invoice.subscription_id == subscription.id
        assert invoice.amount == subscription.pricing.amount
        assert invoice.status == Invoice.Status.PENDING

    def test_idempotent_does_not_create_duplicate(self, subscription, db):
        from apps.billing.models import Invoice
        from apps.subscriptions.renewal import GenerateRenewalInvoiceCommand

        cmd = GenerateRenewalInvoiceCommand()
        cmd.execute(subscription.id)
        result = cmd.execute(subscription.id)  # second call
        assert result is None
        assert Invoice.objects.filter(subscription=subscription).count() == 1

    def test_emits_renewal_invoice_created_outbox_event(self, subscription, db):
        from apps.subscriptions.renewal import GenerateRenewalInvoiceCommand

        GenerateRenewalInvoiceCommand().execute(subscription.id)
        assert OutboxEvent.objects.filter(event_type="renewal_invoice.created").exists()

    def test_returns_none_for_cancelled_subscription(self, subscription, db):
        from apps.subscriptions.renewal import GenerateRenewalInvoiceCommand

        with patch("apps.support.client.ChatwootClient"):
            CancelSubscriptionCommand().execute(subscription.id)
        result = GenerateRenewalInvoiceCommand().execute(subscription.id)
        assert result is None
