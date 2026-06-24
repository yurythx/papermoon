from uuid import UUID

from rest_framework.exceptions import NotFound

from apps.billing.interfaces import AbstractInvoiceWriteRepository
from apps.billing.models import Invoice


class DjangoInvoiceRepository(AbstractInvoiceWriteRepository):
    def create(self, data: dict) -> Invoice:
        return Invoice.objects.create(**data)

    def get_by_id(self, invoice_id: UUID) -> Invoice:
        try:
            return Invoice.objects.get(pk=invoice_id)
        except Invoice.DoesNotExist as exc:
            raise NotFound(f"Invoice {invoice_id} não encontrada.") from exc
