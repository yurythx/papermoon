"""Integration tests for apps/subscriptions/tasks.py.

Tasks run synchronously (no Celery broker) — standard Django test setup.
"""

import datetime

from django.utils import timezone
import pytest

from apps.customers.models import Customer
from apps.products.models import Pricing, Product
from apps.subscriptions.models import Subscription


def _make_subscription(customer: Customer, status: str, expires_delta_days: int) -> Subscription:
    import uuid

    from apps.subscriptions.models import License

    product = Product.objects.create(name="Task Test", slug=f"tt-{uuid.uuid4().hex[:6]}")
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
    expires = timezone.now() + datetime.timedelta(days=expires_delta_days)
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=status,
        starts_at=timezone.now(),
        expires_at=expires,
    )
    License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=expires,
    )
    return sub


# ---------------------------------------------------------------------------
# scan_expiring_subscriptions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScanExpiringSubscriptions:
    def test_active_past_expiry_moves_to_grace_period(self, customer):
        sub = _make_subscription(customer, Subscription.Status.ACTIVE, -1)

        from apps.subscriptions.tasks import scan_expiring_subscriptions

        scan_expiring_subscriptions()

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.GRACE_PERIOD

    def test_active_not_yet_expired_stays_active(self, customer):
        sub = _make_subscription(customer, Subscription.Status.ACTIVE, 5)

        from apps.subscriptions.tasks import scan_expiring_subscriptions

        scan_expiring_subscriptions()

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.ACTIVE

    def test_grace_period_past_grace_deadline_moves_to_expired(self, customer):
        from apps.subscriptions.tasks import GRACE_PERIOD_DAYS

        sub = _make_subscription(
            customer,
            Subscription.Status.GRACE_PERIOD,
            -(GRACE_PERIOD_DAYS + 1),
        )

        from apps.subscriptions.tasks import scan_expiring_subscriptions

        scan_expiring_subscriptions()

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.EXPIRED

    def test_grace_period_within_window_stays_grace(self, customer):
        sub = _make_subscription(customer, Subscription.Status.GRACE_PERIOD, -1)

        from apps.subscriptions.tasks import scan_expiring_subscriptions

        scan_expiring_subscriptions()

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.GRACE_PERIOD

    def test_error_in_one_subscription_does_not_abort_batch(self, customer):
        from unittest.mock import patch

        sub1 = _make_subscription(customer, Subscription.Status.ACTIVE, -1)
        sub2 = _make_subscription(customer, Subscription.Status.ACTIVE, -1)

        call_count = 0

        original_execute = None

        def patched_execute(self_cmd, sub_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("forced error")
            return original_execute(sub_id)

        from apps.subscriptions.commands import ExpireSubscriptionCommand

        original_execute = ExpireSubscriptionCommand().execute

        with patch.object(ExpireSubscriptionCommand, "execute", patched_execute):
            from apps.subscriptions.tasks import scan_expiring_subscriptions

            scan_expiring_subscriptions()

        assert call_count == 2


# ---------------------------------------------------------------------------
# generate_renewal_invoices
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGenerateRenewalInvoices:
    def test_generates_invoice_for_subscription_expiring_within_3_days(self, customer):
        sub = _make_subscription(customer, Subscription.Status.ACTIVE, 2)

        from apps.subscriptions.tasks import generate_renewal_invoices

        generate_renewal_invoices()

        from apps.billing.models import Invoice

        assert Invoice.objects.filter(customer=customer).exists()

    def test_does_not_generate_for_subscription_expiring_in_5_days(self, customer):
        _make_subscription(customer, Subscription.Status.ACTIVE, 5)

        from apps.billing.models import Invoice
        from apps.subscriptions.tasks import generate_renewal_invoices

        generate_renewal_invoices()

        assert not Invoice.objects.filter(customer=customer).exists()

    def test_does_not_generate_for_cancelled_subscription(self, customer):
        _make_subscription(customer, Subscription.Status.CANCELLED, 2)

        from apps.billing.models import Invoice
        from apps.subscriptions.tasks import generate_renewal_invoices

        generate_renewal_invoices()

        assert not Invoice.objects.filter(customer=customer).exists()


# ---------------------------------------------------------------------------
# scan_quota_warnings
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScanQuotaWarnings:
    def _make_quota(self, customer: Customer, max_calls: int, used_calls: int):
        from apps.licensing.models import LicenseQuota

        return LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=max_calls,
            used_api_calls=used_calls,
            reset_at=timezone.now() + datetime.timedelta(days=30),
        )

    def test_emits_outbox_event_at_80_percent(self, customer):
        from shared.models import OutboxEvent

        self._make_quota(customer, 100, 80)

        from apps.subscriptions.tasks import scan_quota_warnings

        scan_quota_warnings()

        assert OutboxEvent.objects.filter(
            event_type="quota.warning",
            payload__customer_id=str(customer.id),
            payload__threshold=80,
        ).exists()

    def test_emits_event_at_90_percent_with_threshold_90(self, customer):
        from shared.models import OutboxEvent

        self._make_quota(customer, 100, 91)

        from apps.subscriptions.tasks import scan_quota_warnings

        scan_quota_warnings()

        event = OutboxEvent.objects.filter(
            event_type="quota.warning",
            payload__customer_id=str(customer.id),
        ).first()
        assert event is not None
        assert event.payload["threshold"] == 90

    def test_no_event_below_80_percent(self, customer):
        from shared.models import OutboxEvent

        self._make_quota(customer, 100, 79)

        from apps.subscriptions.tasks import scan_quota_warnings

        scan_quota_warnings()

        assert not OutboxEvent.objects.filter(event_type="quota.warning").exists()

    def test_skips_quota_with_max_zero(self, customer):
        from shared.models import OutboxEvent

        self._make_quota(customer, 0, 0)

        from apps.subscriptions.tasks import scan_quota_warnings

        scan_quota_warnings()

        assert not OutboxEvent.objects.filter(event_type="quota.warning").exists()


# ---------------------------------------------------------------------------
# scan_expiring_soon
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScanExpiringSoon:
    def test_emits_expiring_soon_for_subscription_expiring_in_7_days(self, customer):
        from shared.models import OutboxEvent

        _make_subscription(customer, Subscription.Status.ACTIVE, 7)

        from apps.subscriptions.tasks import scan_expiring_soon

        scan_expiring_soon()

        assert OutboxEvent.objects.filter(
            event_type="subscription.expiring_soon",
            payload__days_remaining=7,
        ).exists()

    def test_emits_expiring_soon_for_3_days(self, customer):
        from shared.models import OutboxEvent

        _make_subscription(customer, Subscription.Status.ACTIVE, 3)

        from apps.subscriptions.tasks import scan_expiring_soon

        scan_expiring_soon()

        assert OutboxEvent.objects.filter(
            event_type="subscription.expiring_soon",
            payload__days_remaining=3,
        ).exists()

    def test_no_event_for_subscription_expiring_in_30_days(self, customer):
        from shared.models import OutboxEvent

        _make_subscription(customer, Subscription.Status.ACTIVE, 30)

        from apps.subscriptions.tasks import scan_expiring_soon

        scan_expiring_soon()

        assert not OutboxEvent.objects.filter(event_type="subscription.expiring_soon").exists()
