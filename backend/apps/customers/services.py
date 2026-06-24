from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from apps.customers.interfaces import AbstractCustomerRepository
from apps.customers.models import Customer
from shared.exceptions import SubscriptionSuspendedError
from shared.models import OutboxEvent

_TRANSITIONS: dict[str, list[str]] = {
    Customer.Status.ACTIVE: [Customer.Status.SUSPENDED, Customer.Status.CANCELLED],
    Customer.Status.SUSPENDED: [Customer.Status.ACTIVE, Customer.Status.CANCELLED],
    Customer.Status.CANCELLED: [],
}


class CustomerService:
    def __init__(self, repository: AbstractCustomerRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Queries (read-only, no OutboxEvent)
    # ------------------------------------------------------------------

    def list_customers(self) -> QuerySet:
        return self._repo.get_all()

    def get_customer(self, customer_id: UUID) -> Customer:
        return self._repo.get_by_id(customer_id)

    def check_active(self, customer: Customer) -> None:
        if customer.status == Customer.Status.SUSPENDED:
            raise SubscriptionSuspendedError()
        if customer.status == Customer.Status.CANCELLED:
            raise PermissionError("Assinatura cancelada.")

    # ------------------------------------------------------------------
    # Commands (write, always wrapped in transaction + OutboxEvent)
    # ------------------------------------------------------------------

    @transaction.atomic
    def create_customer(self, data: dict) -> Customer:
        customer = self._repo.create(data)
        OutboxEvent.objects.create(
            event_type="customer.created",
            payload={
                "customer_id": str(customer.id),
            },
        )
        return customer

    @transaction.atomic
    def update_customer(self, customer_id: UUID, data: dict) -> Customer:
        allowed = {k: v for k, v in data.items() if k in ("company_name",)}
        return self._repo.update(customer_id, allowed)

    @transaction.atomic
    def suspend_customer(self, customer_id: UUID) -> Customer:
        customer = self._repo.get_by_id(customer_id)
        self._assert_transition(customer, Customer.Status.SUSPENDED)
        customer.status = Customer.Status.SUSPENDED
        self._repo.save(customer)
        OutboxEvent.objects.create(
            event_type="customer.suspended",
            payload={"customer_id": str(customer.id)},
        )
        return customer

    @transaction.atomic
    def reactivate_customer(self, customer_id: UUID) -> Customer:
        customer = self._repo.get_by_id(customer_id)
        self._assert_transition(customer, Customer.Status.ACTIVE)
        customer.status = Customer.Status.ACTIVE
        self._repo.save(customer)
        OutboxEvent.objects.create(
            event_type="customer.reactivated",
            payload={"customer_id": str(customer.id)},
        )
        return customer

    @transaction.atomic
    def cancel_customer(self, customer_id: UUID) -> Customer:
        customer = self._repo.get_by_id(customer_id)
        self._assert_transition(customer, Customer.Status.CANCELLED)
        customer.status = Customer.Status.CANCELLED
        self._repo.save(customer)
        OutboxEvent.objects.create(
            event_type="customer.cancelled",
            payload={"customer_id": str(customer.id)},
        )
        return customer

    @transaction.atomic
    def soft_delete_customer(self, customer_id: UUID) -> Customer:
        customer = self._repo.get_any_by_id(customer_id)
        if customer.is_deleted:
            raise ValueError("Customer já foi deletado.")
        customer.soft_delete()
        return customer

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _assert_transition(self, customer: Customer, target: str) -> None:
        allowed = _TRANSITIONS.get(customer.status, [])
        if target not in allowed:
            raise ValueError(f"Transição inválida: {customer.status} → {target}.")
