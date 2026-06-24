"""Unit tests for reset_quota_monthly Celery task."""

from datetime import timedelta

from django.utils import timezone
import pytest

from apps.customers.models import Customer
from apps.licensing.models import LicenseQuota
from apps.licensing.tasks import reset_quota_monthly


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        company_name="Quota Co",
        document="11222333000199",
        status=Customer.Status.ACTIVE,
    )


def _quota(customer, used, reset_delta_days):
    return LicenseQuota.objects.create(
        customer=customer,
        max_api_calls=1000,
        used_api_calls=used,
        reset_at=timezone.now() + timedelta(days=reset_delta_days),
    )


@pytest.mark.django_db
class TestResetQuotaMonthly:
    def test_expired_quota_is_zeroed(self, customer):
        q = _quota(customer, used=500, reset_delta_days=-1)
        reset_quota_monthly()
        q.refresh_from_db()
        assert q.used_api_calls == 0

    def test_reset_at_advances_by_one_month(self, customer):
        # Use March 1 of the current year (always in the past since we run after March)
        now = timezone.now()
        past_march = now.replace(month=3, day=1, hour=0, minute=0, second=0, microsecond=0)
        q = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=100,
            reset_at=past_march,
        )
        reset_quota_monthly()
        q.refresh_from_db()
        assert q.reset_at.month == 4

    def test_reset_at_wraps_december_to_january(self, customer):
        now = timezone.now()
        # Use December of last year so reset_at is guaranteed to be in the past
        past_december = now.replace(year=now.year - 1, month=12, day=1)
        q = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=100,
            reset_at=past_december,
        )
        reset_quota_monthly()
        q.refresh_from_db()
        assert q.reset_at.month == 1
        assert q.reset_at.year == now.year

    def test_future_quota_is_not_reset(self, customer):
        q = _quota(customer, used=800, reset_delta_days=+15)
        reset_quota_monthly()
        q.refresh_from_db()
        assert q.used_api_calls == 800

    def test_multiple_quotas_only_expired_are_reset(self, db):
        c1 = Customer.objects.create(
            company_name="A", document="11111111000111", status=Customer.Status.ACTIVE
        )
        c2 = Customer.objects.create(
            company_name="B", document="22222222000122", status=Customer.Status.ACTIVE
        )
        q_expired = _quota(c1, used=300, reset_delta_days=-1)
        q_future = _quota(c2, used=700, reset_delta_days=+10)

        reset_quota_monthly()

        q_expired.refresh_from_db()
        q_future.refresh_from_db()
        assert q_expired.used_api_calls == 0
        assert q_future.used_api_calls == 700
