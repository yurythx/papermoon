"""Unit tests for shared/permissions.py — IsActiveCustomer.

Tests call has_permission() directly with realistic mock requests backed
by real DB objects so no API routing overhead is needed.
"""

from unittest.mock import MagicMock

import pytest

from apps.accounts.models import CustomUser
from apps.customers.models import Customer, CustomerProfile
from shared.permissions import IsActiveCustomer


def _make_user(suffix: str) -> CustomUser:
    email = f"perm_{suffix}@unit.com"
    return CustomUser.objects.create_user(username=f"perm_{suffix}", email=email, password="x")


def _mock_request(user) -> MagicMock:
    req = MagicMock()
    req.user = user
    return req


def _link_customer(user: CustomUser, status: str, doc_suffix: str) -> Customer:
    customer = Customer.objects.create(
        company_name="Perm Unit Co",
        document=f"{doc_suffix}.000.000/0001-01",
        status=status,
    )
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)
    return customer


# ---------------------------------------------------------------------------
# has_permission() scenarios
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIsActiveCustomerPermission:
    def test_unauthenticated_user_returns_true(self):
        perm = IsActiveCustomer()
        req = MagicMock()
        req.user = MagicMock()
        req.user.is_authenticated = False
        assert perm.has_permission(req, None) is True

    def test_none_user_returns_true(self):
        perm = IsActiveCustomer()
        req = MagicMock()
        req.user = None
        assert perm.has_permission(req, None) is True

    def test_staff_user_returns_true_regardless_of_customer(self):
        perm = IsActiveCustomer()
        user = _make_user("staff")
        user.is_staff = True
        user.save()
        req = _mock_request(user)
        assert perm.has_permission(req, None) is True

    def test_user_with_no_profile_returns_true(self):
        perm = IsActiveCustomer()
        user = _make_user("noprofile")
        req = _mock_request(user)
        assert perm.has_permission(req, None) is True

    def test_active_customer_returns_true(self):
        perm = IsActiveCustomer()
        user = _make_user("active")
        _link_customer(user, Customer.Status.ACTIVE, "70")
        req = _mock_request(user)
        assert perm.has_permission(req, None) is True

    def test_suspended_customer_raises_subscription_suspended_error(self):
        from shared.exceptions import SubscriptionSuspendedError

        perm = IsActiveCustomer()
        user = _make_user("suspended")
        _link_customer(user, Customer.Status.SUSPENDED, "71")
        req = _mock_request(user)
        with pytest.raises(SubscriptionSuspendedError):
            perm.has_permission(req, None)

    def test_cancelled_customer_returns_false(self):
        perm = IsActiveCustomer()
        user = _make_user("cancelled")
        _link_customer(user, Customer.Status.CANCELLED, "72")
        req = _mock_request(user)
        result = perm.has_permission(req, None)
        assert result is False

    def test_cancelled_sets_message(self):
        perm = IsActiveCustomer()
        user = _make_user("cancelled2")
        _link_customer(user, Customer.Status.CANCELLED, "73")
        req = _mock_request(user)
        perm.has_permission(req, None)
        assert "cancelada" in perm.message.lower()
