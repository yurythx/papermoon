from abc import ABC, abstractmethod
from uuid import UUID

from apps.billing.models import Invoice


class AbstractInvoiceWriteRepository(ABC):
    @abstractmethod
    def create(self, data: dict) -> Invoice: ...

    @abstractmethod
    def get_by_id(self, invoice_id: UUID) -> Invoice: ...
