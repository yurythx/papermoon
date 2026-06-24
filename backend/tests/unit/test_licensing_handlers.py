"""Unit tests for apps.licensing.handlers — quota sync logic."""

import datetime

from django.utils import timezone
import pytest


@pytest.mark.django_db
class TestSyncQuotaFromSubscription:
    def _make_subscription(self, customer, max_api_calls=5000):
        from apps.products.models import Pricing, Product
        from apps.subscriptions.models import Subscription

        product = Product.objects.create(name="Plano Pro", slug="pro-test")
        pricing = Pricing.objects.create(
            product=product,
            billing_cycle="monthly",
            amount="199.00",
            max_api_calls=max_api_calls,
        )
        return Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=timezone.now(),
            expires_at=timezone.now() + datetime.timedelta(days=30),
        )

    def test_updates_quota_to_pricing_limit(self, customer):
        from apps.licensing.handlers import sync_quota_from_subscription
        from apps.licensing.models import LicenseQuota

        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=10000,
            used_api_calls=0,
            reset_at=timezone.now() + datetime.timedelta(days=30),
        )
        sub = self._make_subscription(customer, max_api_calls=50000)

        sync_quota_from_subscription(
            {"subscription_id": str(sub.id), "customer_id": str(customer.id)},
            event_id="evt-1",
        )

        quota = LicenseQuota.objects.get(customer=customer)
        assert quota.max_api_calls == 50000

    def test_noop_when_pricing_max_api_calls_is_zero(self, customer):
        from apps.licensing.handlers import sync_quota_from_subscription
        from apps.licensing.models import LicenseQuota

        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=10000,
            used_api_calls=0,
            reset_at=timezone.now() + datetime.timedelta(days=30),
        )
        sub = self._make_subscription(customer, max_api_calls=0)

        sync_quota_from_subscription(
            {"subscription_id": str(sub.id), "customer_id": str(customer.id)},
            event_id="evt-2",
        )

        quota = LicenseQuota.objects.get(customer=customer)
        assert quota.max_api_calls == 10000  # unchanged

    def test_missing_subscription_id_is_noop(self, customer):
        from apps.licensing.handlers import sync_quota_from_subscription
        from apps.licensing.models import LicenseQuota

        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=10000,
            used_api_calls=0,
            reset_at=timezone.now() + datetime.timedelta(days=30),
        )

        sync_quota_from_subscription({}, event_id="evt-3")  # no subscription_id key

        quota = LicenseQuota.objects.get(customer=customer)
        assert quota.max_api_calls == 10000  # unchanged

    def test_nonexistent_subscription_is_noop(self, customer):
        from apps.licensing.handlers import sync_quota_from_subscription
        from apps.licensing.models import LicenseQuota

        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=10000,
            used_api_calls=0,
            reset_at=timezone.now() + datetime.timedelta(days=30),
        )

        sync_quota_from_subscription(
            {"subscription_id": "00000000-0000-0000-0000-000000000000"},
            event_id="evt-4",
        )

        quota = LicenseQuota.objects.get(customer=customer)
        assert quota.max_api_calls == 10000  # unchanged
