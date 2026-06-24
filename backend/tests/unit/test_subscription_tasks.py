"""Unit tests for subscription lifecycle Celery tasks."""

from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
import pytest

from apps.customers.models import Customer
from apps.licensing.models import LicenseQuota
from apps.products.models import Pricing, Product
from apps.subscriptions.models import Subscription
from apps.subscriptions.tasks import (
    scan_expiring_soon,
    scan_expiring_subscriptions,
    scan_quota_warnings,
)
from shared.models import OutboxEvent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        company_name="Tasks Co",
        document="11222333000181",
        status=Customer.Status.ACTIVE,
    )


@pytest.fixture
def product(db):
    return Product.objects.create(name="Pro", slug="pro", description="")


@pytest.fixture
def pricing(db, product):
    return Pricing.objects.create(
        product=product,
        billing_cycle=Pricing.BillingCycle.MONTHLY,
        amount="99.00",
        max_api_calls=1000,
    )


@pytest.fixture
def active_subscription(db, customer, product, pricing):
    now = timezone.now()
    return Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=now - timedelta(days=30),
        expires_at=now - timedelta(hours=1),  # already expired
    )


@pytest.fixture
def grace_subscription(db, customer, product, pricing):
    now = timezone.now()
    return Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.GRACE_PERIOD,
        starts_at=now - timedelta(days=33),
        expires_at=now - timedelta(days=4),  # past grace period
    )


# ---------------------------------------------------------------------------
# scan_expiring_subscriptions
# ---------------------------------------------------------------------------


_CMD_PATH = "apps.subscriptions.commands.ExpireSubscriptionCommand"


@pytest.mark.django_db
class TestScanExpiringSubscriptions:
    def test_active_past_expiry_triggers_expire_command(self, active_subscription):
        with patch(_CMD_PATH) as MockCmd:
            mock_instance = MockCmd.return_value
            scan_expiring_subscriptions()
            mock_instance.execute.assert_called_once_with(active_subscription.id)

    def test_grace_past_deadline_triggers_expire_command(self, grace_subscription):
        with patch(_CMD_PATH) as MockCmd:
            mock_instance = MockCmd.return_value
            scan_expiring_subscriptions()
            mock_instance.execute.assert_called_once_with(grace_subscription.id)

    def test_active_not_yet_expired_is_skipped(self, customer, product, pricing):
        now = timezone.now()
        Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=5),
        )
        with patch(_CMD_PATH) as MockCmd:
            scan_expiring_subscriptions()
            MockCmd.return_value.execute.assert_not_called()

    def test_command_error_is_caught_and_does_not_abort_loop(self, customer, product, pricing):
        now = timezone.now()
        Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=now - timedelta(days=30),
            expires_at=now - timedelta(hours=2),
        )
        Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=now - timedelta(days=31),
            expires_at=now - timedelta(hours=3),
        )
        with patch(_CMD_PATH) as MockCmd:
            mock_instance = MockCmd.return_value
            mock_instance.execute.side_effect = [Exception("fail"), None]
            scan_expiring_subscriptions()
            assert mock_instance.execute.call_count == 2


# ---------------------------------------------------------------------------
# scan_quota_warnings
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScanQuotaWarnings:
    def test_quota_at_80pct_emits_outbox_event(self, customer):
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=100,
            used_api_calls=80,
            reset_at=timezone.now() + timedelta(days=30),
        )
        scan_quota_warnings()
        event = OutboxEvent.objects.filter(
            event_type="quota.warning",
            payload__customer_id=str(customer.id),
        ).first()
        assert event is not None
        assert event.payload["threshold"] == 80

    def test_quota_at_90pct_emits_90_threshold(self, customer):
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=100,
            used_api_calls=91,
            reset_at=timezone.now() + timedelta(days=30),
        )
        scan_quota_warnings()
        event = OutboxEvent.objects.filter(
            event_type="quota.warning",
            payload__customer_id=str(customer.id),
        ).first()
        assert event is not None
        assert event.payload["threshold"] == 90

    def test_quota_below_80pct_emits_no_event(self, customer):
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=100,
            used_api_calls=79,
            reset_at=timezone.now() + timedelta(days=30),
        )
        scan_quota_warnings()
        assert not OutboxEvent.objects.filter(event_type="quota.warning").exists()

    def test_quota_zero_max_is_skipped(self, customer):
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=0,
            used_api_calls=0,
            reset_at=timezone.now() + timedelta(days=30),
        )
        scan_quota_warnings()
        assert not OutboxEvent.objects.filter(event_type="quota.warning").exists()


# ---------------------------------------------------------------------------
# scan_expiring_soon
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScanExpiringSoon:
    def _make_sub(self, customer, product, pricing, expires_at):
        now = timezone.now()
        return Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=now - timedelta(days=30),
            expires_at=expires_at,
        )

    def test_sub_expiring_in_1_day_emits_event(self, customer, product, pricing):
        now = timezone.now()
        self._make_sub(customer, product, pricing, expires_at=now + timedelta(hours=12))
        scan_expiring_soon()
        event = OutboxEvent.objects.filter(event_type="subscription.expiring_soon").first()
        assert event is not None
        assert event.payload["days_remaining"] == 1

    def test_sub_expiring_in_7_days_emits_event(self, customer, product, pricing):
        now = timezone.now()
        self._make_sub(customer, product, pricing, expires_at=now + timedelta(days=6, hours=12))
        scan_expiring_soon()
        event = OutboxEvent.objects.filter(event_type="subscription.expiring_soon").first()
        assert event is not None
        assert event.payload["days_remaining"] == 7

    def test_already_expired_sub_not_matched(self, customer, product, pricing):
        now = timezone.now()
        self._make_sub(customer, product, pricing, expires_at=now - timedelta(hours=1))
        scan_expiring_soon()
        assert not OutboxEvent.objects.filter(event_type="subscription.expiring_soon").exists()

    def test_non_active_sub_not_matched(self, customer, product, pricing):
        now = timezone.now()
        Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.GRACE_PERIOD,
            starts_at=now - timedelta(days=30),
            expires_at=now + timedelta(hours=12),
        )
        scan_expiring_soon()
        assert not OutboxEvent.objects.filter(event_type="subscription.expiring_soon").exists()

    def test_payload_contains_subscription_id_and_customer_id(self, customer, product, pricing):
        now = timezone.now()
        sub = self._make_sub(customer, product, pricing, expires_at=now + timedelta(hours=12))
        scan_expiring_soon()
        event = OutboxEvent.objects.filter(event_type="subscription.expiring_soon").first()
        assert event is not None
        assert event.payload["subscription_id"] == str(sub.id)
        assert event.payload["customer_id"] == str(customer.id)
