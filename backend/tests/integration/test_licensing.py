import pytest
from rest_framework.test import APIClient

from apps.licensing.models import ApiKey, LicenseQuota

_KEYS_URL = "/api/v1/client/api-keys/"


# ---------------------------------------------------------------------------
# Legacy fixture (kept for original tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return APIClient()


# ---------------------------------------------------------------------------
# Original tests (kept intact)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateKeyEndpoint:
    def test_invalid_key_returns_valid_false(self, client):
        response = client.get("/api/v1/licensing/validate-key/?key=chave_invalida")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is False

    def test_missing_key_param_returns_400(self, client):
        response = client.get("/api/v1/licensing/validate-key/")
        assert response.status_code == 400

    def test_valid_active_key_returns_valid_true(self, client, db):
        from datetime import timedelta

        from django.utils import timezone

        from apps.customers.models import Customer
        from tests.conftest import create_active_license

        customer = Customer.objects.create(
            company_name="Teste Licensing",
            document="55.555.555/0001-55",
        )
        api_key = ApiKey.objects.create(customer=customer)
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=100,
            used_api_calls=0,
            reset_at=timezone.now() + timedelta(days=30),
        )
        create_active_license(customer)

        response = client.get(f"/api/v1/licensing/validate-key/?key={api_key.key}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["valid"] is True
        assert data["data"]["quota_remaining"] == 99  # decrementou 1


# ---------------------------------------------------------------------------
# Extended tests (using shared conftest fixtures)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateKeyExtended:
    def test_inactive_key_returns_valid_false(self, api_client, api_key):
        api_key.is_active = False
        api_key.save()
        resp = api_client.get(f"/api/v1/licensing/validate-key/?key={api_key.key}")
        assert resp.json()["data"]["valid"] is False

    def test_valid_key_increments_used_calls(self, api_client, api_key):
        before = LicenseQuota.objects.get(customer=api_key.customer).used_api_calls
        api_client.get(f"/api/v1/licensing/validate-key/?key={api_key.key}")
        after = LicenseQuota.objects.get(customer=api_key.customer).used_api_calls
        assert after == before + 1

    def test_validate_returns_quota_remaining_field(self, api_client, api_key):
        resp = api_client.get(f"/api/v1/licensing/validate-key/?key={api_key.key}")
        assert "quota_remaining" in resp.json()["data"]

    def test_two_calls_return_consistent_valid_result(self, api_client, api_key):
        # Clear cache between calls so we go through DB path both times
        from django.core.cache import cache

        cache.clear()
        r1 = api_client.get(f"/api/v1/licensing/validate-key/?key={api_key.key}")
        cache.clear()
        r2 = api_client.get(f"/api/v1/licensing/validate-key/?key={api_key.key}")
        assert r1.json()["data"]["valid"] == r2.json()["data"]["valid"]


@pytest.mark.django_db
class TestApiKeyManagement:
    def test_client_can_list_own_api_keys(self, customer_client, customer_with_profile):
        ApiKey.objects.create(customer=customer_with_profile)
        resp = customer_client.get(_KEYS_URL)
        assert resp.status_code == 200
        # ApiKeyListCreateView returns plain list (no paginator)
        assert len(resp.json()["data"]) >= 1

    def test_client_creates_new_api_key(self, customer_client, customer_with_profile):
        resp = customer_client.post(_KEYS_URL, {}, format="json")
        assert resp.status_code == 201
        assert "key" in resp.json()["data"]

    def test_client_revokes_api_key(self, customer_client, customer_with_profile):
        key = ApiKey.objects.create(customer=customer_with_profile)
        resp = customer_client.delete(f"{_KEYS_URL}{key.id}/")
        assert resp.status_code == 204
        key.refresh_from_db()
        assert key.is_active is False

    def test_revoked_key_fails_validation(self, api_client, customer_client, customer_with_profile):
        from django.core.cache import cache

        key = ApiKey.objects.create(customer=customer_with_profile)
        customer_client.delete(f"{_KEYS_URL}{key.id}/")
        # Cache is cleared on revoke, so DB path is used
        cache.clear()
        resp = api_client.get(f"/api/v1/licensing/validate-key/?key={key.key}")
        assert resp.json()["data"]["valid"] is False

    def test_client_cannot_access_other_tenants_api_keys(self, customer_client, api_key):
        resp = customer_client.get(_KEYS_URL)
        # api_key belongs to `customer`, not `customer_with_profile`
        key_ids = [str(k["id"]) for k in resp.json()["data"]]
        assert str(api_key.id) not in key_ids

    def test_unauthenticated_cannot_list_keys(self, api_client):
        resp = api_client.get(_KEYS_URL)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# ValidateKey — cache and edge-case coverage
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateKeyCachePaths:
    def setup_method(self):
        from django.core.cache import cache

        cache.clear()

    def test_cache_hit_returns_cached_result(self, api_client, api_key):
        from django.core.cache import cache

        # Populate cache manually
        cache.set(f"apikey:{api_key.key}", {"valid": True, "quota_remaining": 42}, timeout=60)

        resp = api_client.get(f"/api/v1/licensing/validate-key/?key={api_key.key}")
        assert resp.status_code == 200
        assert resp.json()["data"]["quota_remaining"] == 42

    def test_no_active_license_returns_invalid(self, api_client, customer):
        from apps.licensing.models import ApiKey

        key = ApiKey.objects.create(customer=customer)
        resp = api_client.get(f"/api/v1/licensing/validate-key/?key={key.key}")
        data = resp.json()["data"]
        assert data["valid"] is False
        assert data["reason"] == "no_active_license"

    def test_no_quota_returns_valid_none(self, api_client, customer):
        from apps.licensing.models import ApiKey
        from tests.conftest import create_active_license

        key = ApiKey.objects.create(customer=customer)
        create_active_license(customer)
        # No LicenseQuota created

        resp = api_client.get(f"/api/v1/licensing/validate-key/?key={key.key}")
        data = resp.json()["data"]
        assert data["valid"] is True
        assert data["quota_remaining"] is None

    def test_quota_exceeded_returns_invalid(self, api_client, customer):
        import datetime

        from django.utils import timezone

        from apps.licensing.models import ApiKey, LicenseQuota
        from tests.conftest import create_active_license

        key = ApiKey.objects.create(customer=customer)
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=5,
            used_api_calls=5,
            reset_at=timezone.now() + datetime.timedelta(days=30),
        )
        create_active_license(customer)

        resp = api_client.get(f"/api/v1/licensing/validate-key/?key={key.key}")
        data = resp.json()["data"]
        assert data["valid"] is False
        assert data["reason"] == "quota_exceeded"
        assert data["quota_remaining"] == 0

    def test_invalid_key_is_cached(self, api_client):
        from django.core.cache import cache

        cache.clear()
        api_client.get("/api/v1/licensing/validate-key/?key=fake_key_xyz")
        assert cache.get("apikey:fake_key_xyz") is not None


# ---------------------------------------------------------------------------
# ApiKey list/create — no-profile edge cases
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestApiKeyNoProfile:
    def test_list_returns_empty_when_no_profile(self, api_client, regular_user):
        # Authenticate a user with no CustomerProfile attached
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.get(_KEYS_URL)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_create_returns_400_when_no_profile(self, api_client, regular_user):
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.post(_KEYS_URL, {}, format="json")
        assert resp.status_code == 400

    def test_delete_returns_404_when_no_profile(self, api_client, regular_user):
        import uuid

        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.delete(f"{_KEYS_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404

    def test_delete_returns_404_for_wrong_key_id(self, customer_client, customer_with_profile):
        import uuid

        resp = customer_client.delete(f"{_KEYS_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# snapshot_daily_api_usage / reset_quota_monthly beat tasks
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSnapshotDailyApiUsage:
    def _make_customer(self, doc: str):
        from apps.customers.models import Customer

        return Customer.objects.create(company_name=f"Snapshot Corp {doc[:4]}", document=doc)

    def test_creates_daily_usage_row_per_customer(self):
        import datetime

        from apps.licensing.models import DailyApiUsage
        from apps.licensing.tasks import snapshot_daily_api_usage

        customer = self._make_customer("70.000.000/0001-70")
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=42,
            reset_at=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
        )

        snapshot_daily_api_usage()

        row = DailyApiUsage.objects.get(customer=customer, date=datetime.date.today())
        assert row.calls_count == 42

    def test_rerun_same_day_updates_existing_row(self):
        import datetime

        from apps.licensing.models import DailyApiUsage
        from apps.licensing.tasks import snapshot_daily_api_usage

        customer = self._make_customer("71.000.000/0001-71")
        quota = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=10,
            reset_at=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
        )

        snapshot_daily_api_usage()
        quota.used_api_calls = 25
        quota.save()
        snapshot_daily_api_usage()

        rows = DailyApiUsage.objects.filter(customer=customer, date=datetime.date.today())
        assert rows.count() == 1
        assert rows.first().calls_count == 25

    def test_no_quotas_does_not_raise(self):
        from apps.licensing.tasks import snapshot_daily_api_usage

        snapshot_daily_api_usage()


@pytest.mark.django_db
class TestResetQuotaMonthly:
    def _make_customer(self, doc: str):
        from apps.customers.models import Customer

        return Customer.objects.create(company_name=f"Reset Corp {doc[:4]}", document=doc)

    def test_resets_used_calls_when_reset_at_passed(self):
        import datetime

        from django.utils import timezone

        from apps.licensing.tasks import reset_quota_monthly

        customer = self._make_customer("72.000.000/0001-72")
        quota = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=999,
            reset_at=timezone.now() - datetime.timedelta(days=1),
        )

        reset_quota_monthly()

        quota.refresh_from_db()
        assert quota.used_api_calls == 0

    def test_advances_reset_at_to_next_month(self):
        from django.utils import timezone

        from apps.licensing.tasks import reset_quota_monthly

        customer = self._make_customer("73.000.000/0001-73")
        old_reset_at = timezone.now().replace(year=2000, month=5, day=1)
        quota = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=500,
            reset_at=old_reset_at,
        )

        reset_quota_monthly()

        quota.refresh_from_db()
        assert quota.reset_at > old_reset_at
        assert quota.reset_at.month == 6

    def test_rollover_from_day_31_into_shorter_month_does_not_crash(self):
        """Regression test: reset_at on the 31st rolling into a 30-day month
        used to crash with ValueError('day is out of range for month')."""
        from django.utils import timezone

        from apps.licensing.tasks import reset_quota_monthly

        customer = self._make_customer("76.000.000/0001-76")
        past_jan_31 = timezone.now().replace(year=2000, month=1, day=31)
        quota = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=500,
            reset_at=past_jan_31,
        )

        reset_quota_monthly()

        quota.refresh_from_db()
        assert quota.reset_at.month == 2
        assert quota.reset_at.day == 1

    def test_december_rollover_advances_to_january_next_year(self):
        from django.utils import timezone

        from apps.licensing.tasks import reset_quota_monthly

        customer = self._make_customer("74.000.000/0001-74")
        past_december = timezone.now().replace(year=2000, month=12, day=1)
        quota = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=300,
            reset_at=past_december,
        )

        reset_quota_monthly()

        quota.refresh_from_db()
        assert quota.reset_at.year == 2001
        assert quota.reset_at.month == 1

    def test_future_reset_at_not_touched(self):
        import datetime

        from django.utils import timezone

        from apps.licensing.tasks import reset_quota_monthly

        customer = self._make_customer("75.000.000/0001-75")
        future = timezone.now() + datetime.timedelta(days=30)
        quota = LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=1000,
            used_api_calls=777,
            reset_at=future,
        )

        reset_quota_monthly()

        quota.refresh_from_db()
        assert quota.used_api_calls == 777
