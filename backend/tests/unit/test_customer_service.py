from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.customers.models import Customer
from apps.customers.services import CustomerService
from shared.exceptions import SubscriptionSuspendedError


def _make_customer(status: str = Customer.Status.ACTIVE) -> Customer:
    c = Customer()
    c.id = uuid4()
    c.company_name = "Empresa Teste"
    c.document = "00.000.000/0001-00"
    c.status = status
    return c


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    return CustomerService(repo)


# ---------------------------------------------------------------------------
# create_customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerServiceCreate:
    def test_creates_customer_and_outbox_event(self, service, repo):
        customer = _make_customer()
        repo.create.return_value = customer

        with patch("apps.customers.services.OutboxEvent.objects.create") as mock_outbox:
            result = service.create_customer(
                {"company_name": "X", "document": "00.000.000/0001-00"}
            )

        repo.create.assert_called_once()
        mock_outbox.assert_called_once_with(
            event_type="customer.created",
            payload={"customer_id": str(customer.id)},
        )
        assert result == customer


# ---------------------------------------------------------------------------
# update_customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerServiceUpdate:
    def test_update_strips_forbidden_fields(self, service, repo):
        customer = _make_customer()
        repo.update.return_value = customer

        service.update_customer(customer.id, {"company_name": "Nova", "status": "cancelled"})

        # status must not reach the repo
        call_kwargs = repo.update.call_args[0][1]
        assert "status" not in call_kwargs
        assert call_kwargs["company_name"] == "Nova"


# ---------------------------------------------------------------------------
# suspend_customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerServiceSuspend:
    def test_suspend_active_customer_succeeds(self, service, repo):
        customer = _make_customer(Customer.Status.ACTIVE)
        repo.get_by_id.return_value = customer

        with patch("apps.customers.services.OutboxEvent.objects.create"):
            result = service.suspend_customer(customer.id)

        repo.save.assert_called_once_with(customer)
        assert result.status == Customer.Status.SUSPENDED

    def test_suspend_already_suspended_raises(self, service, repo):
        customer = _make_customer(Customer.Status.SUSPENDED)
        repo.get_by_id.return_value = customer

        with pytest.raises(ValueError, match="Transição inválida"):
            service.suspend_customer(customer.id)

    def test_suspend_cancelled_raises(self, service, repo):
        customer = _make_customer(Customer.Status.CANCELLED)
        repo.get_by_id.return_value = customer

        with pytest.raises(ValueError, match="Transição inválida"):
            service.suspend_customer(customer.id)

    def test_suspend_emits_customer_suspended_event(self, service, repo):
        customer = _make_customer(Customer.Status.ACTIVE)
        repo.get_by_id.return_value = customer

        with patch("apps.customers.services.OutboxEvent.objects.create") as mock_outbox:
            service.suspend_customer(customer.id)

        mock_outbox.assert_called_once_with(
            event_type="customer.suspended",
            payload={"customer_id": str(customer.id)},
        )


# ---------------------------------------------------------------------------
# reactivate_customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerServiceReactivate:
    def test_reactivate_suspended_customer_succeeds(self, service, repo):
        customer = _make_customer(Customer.Status.SUSPENDED)
        repo.get_by_id.return_value = customer

        with patch("apps.customers.services.OutboxEvent.objects.create"):
            result = service.reactivate_customer(customer.id)

        assert result.status == Customer.Status.ACTIVE

    def test_reactivate_active_raises(self, service, repo):
        customer = _make_customer(Customer.Status.ACTIVE)
        repo.get_by_id.return_value = customer

        with pytest.raises(ValueError, match="Transição inválida"):
            service.reactivate_customer(customer.id)

    def test_reactivate_cancelled_raises(self, service, repo):
        customer = _make_customer(Customer.Status.CANCELLED)
        repo.get_by_id.return_value = customer

        with pytest.raises(ValueError, match="Transição inválida"):
            service.reactivate_customer(customer.id)

    def test_reactivate_emits_customer_reactivated_event(self, service, repo):
        customer = _make_customer(Customer.Status.SUSPENDED)
        repo.get_by_id.return_value = customer

        with patch("apps.customers.services.OutboxEvent.objects.create") as mock_outbox:
            service.reactivate_customer(customer.id)

        mock_outbox.assert_called_once_with(
            event_type="customer.reactivated",
            payload={"customer_id": str(customer.id)},
        )


# ---------------------------------------------------------------------------
# cancel_customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerServiceCancel:
    def test_cancel_active_customer_succeeds(self, service, repo):
        customer = _make_customer(Customer.Status.ACTIVE)
        repo.get_by_id.return_value = customer

        with patch("apps.customers.services.OutboxEvent.objects.create"):
            result = service.cancel_customer(customer.id)

        assert result.status == Customer.Status.CANCELLED

    def test_cancel_already_cancelled_raises(self, service, repo):
        customer = _make_customer(Customer.Status.CANCELLED)
        repo.get_by_id.return_value = customer

        with pytest.raises(ValueError, match="Transição inválida"):
            service.cancel_customer(customer.id)

    def test_cancel_emits_customer_cancelled_event(self, service, repo):
        customer = _make_customer(Customer.Status.ACTIVE)
        repo.get_by_id.return_value = customer

        with patch("apps.customers.services.OutboxEvent.objects.create") as mock_outbox:
            service.cancel_customer(customer.id)

        mock_outbox.assert_called_once_with(
            event_type="customer.cancelled",
            payload={"customer_id": str(customer.id)},
        )


# ---------------------------------------------------------------------------
# check_active
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerServiceCheckActive:
    def test_active_customer_passes(self, service):
        customer = _make_customer(Customer.Status.ACTIVE)
        service.check_active(customer)  # must not raise

    def test_suspended_customer_raises_subscription_exception(self, service):
        customer = _make_customer(Customer.Status.SUSPENDED)
        with pytest.raises(SubscriptionSuspendedError):
            service.check_active(customer)

    def test_cancelled_customer_raises_permission_error(self, service):
        customer = _make_customer(Customer.Status.CANCELLED)
        with pytest.raises(PermissionError):
            service.check_active(customer)


# ---------------------------------------------------------------------------
# list / get
# ---------------------------------------------------------------------------


class TestCustomerServiceQueries:
    def test_list_customers_delegates_to_repo(self, service, repo):
        service.list_customers()
        repo.get_all.assert_called_once()

    def test_get_customer_delegates_to_repo(self, service, repo):
        service.get_customer("some-id")
        repo.get_by_id.assert_called_once_with("some-id")
