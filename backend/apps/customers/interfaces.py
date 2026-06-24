from abc import ABC, abstractmethod
from uuid import UUID

from django.db.models import QuerySet

from apps.customers.models import Customer


class AbstractCustomerReadRepository(ABC):
    """Read side of CQRS — no state mutations allowed."""

    @abstractmethod
    def get_by_id(self, customer_id: UUID) -> Customer: ...

    @abstractmethod
    def get_all(self) -> QuerySet: ...

    @abstractmethod
    def get_any_by_id(self, customer_id: UUID) -> Customer:
        """Like get_by_id but includes soft-deleted records (needed for soft-delete ops)."""
        ...


class AbstractCustomerWriteRepository(ABC):
    """Write side of CQRS — owns all mutations."""

    @abstractmethod
    def create(self, data: dict) -> Customer: ...

    @abstractmethod
    def update(self, customer_id: UUID, data: dict) -> Customer: ...

    @abstractmethod
    def save(self, customer: Customer) -> Customer:
        """Persist an already-loaded entity (used by service state transitions)."""
        ...


class AbstractCustomerRepository(AbstractCustomerReadRepository, AbstractCustomerWriteRepository):
    """Combined repository interface injected into CustomerService."""
