import datetime
import logging
from uuid import UUID

from django.db import transaction
from rest_framework.exceptions import NotFound

from apps.billing.interfaces import AbstractInvoiceWriteRepository
from apps.billing.models import Invoice
from shared.models import OutboxEvent
from shared.public_urls import sanitize_payment_url

logger = logging.getLogger(__name__)


class RegisterChargeCommand:
    """
    Registers an invoice as a charge in the payment gateway and persists the gateway ID.

    The external HTTP call happens OUTSIDE the transaction to avoid holding a DB lock
    during a network round-trip. The atomic write is short: only the DB update + OutboxEvent.
    Idempotent: if asaas_id is already set the command is a no-op.
    """

    def __init__(self, invoice_id: UUID, gateway) -> None:
        self._invoice_id = invoice_id
        self._gateway = gateway

    def execute(self) -> Invoice:
        invoice = Invoice.objects.get(pk=self._invoice_id)

        if invoice.asaas_id:
            return invoice  # Already registered — idempotent

        # External HTTP call intentionally outside the atomic block.
        result = self._gateway.create_charge(invoice.customer, invoice)
        asaas_id = result.get("id", "")
        # invoiceUrl is the Asaas-hosted payment page (works for boleto and PIX).
        payment_url = sanitize_payment_url(
            result.get("invoiceUrl") or result.get("bankSlipUrl") or ""
        ) or ""

        with transaction.atomic():
            invoice = Invoice.objects.select_for_update(skip_locked=True).get(pk=self._invoice_id)
            invoice.asaas_id = asaas_id
            invoice.payment_url = payment_url
            invoice.save()
            OutboxEvent.objects.create(
                event_type="charge.registered",
                payload={
                    "invoice_id": str(invoice.id),
                    "customer_id": str(invoice.customer_id),
                    "asaas_id": asaas_id,
                },
            )
        return invoice


class ConfirmPaymentCommand:
    """
    Marks an invoice as PAID. Called from the Asaas webhook on PAYMENT_RECEIVED.

    No external HTTP calls — Asaas already confirmed the payment by calling us.
    Idempotent: repeated calls on an already-PAID invoice are safe no-ops.
    """

    def __init__(self, invoice_id: UUID) -> None:
        self._invoice_id = invoice_id

    @transaction.atomic
    def execute(self) -> Invoice:
        try:
            invoice = Invoice.objects.select_for_update(skip_locked=True).get(pk=self._invoice_id)
        except Invoice.DoesNotExist as exc:
            raise NotFound(f"Invoice {self._invoice_id} não encontrada.") from exc

        if invoice.status == Invoice.Status.PAID:
            return invoice  # Idempotent — webhook may be replayed

        invoice.status = Invoice.Status.PAID
        invoice.save()

        payload: dict = {
            "invoice_id": str(invoice.id),
            "customer_id": str(invoice.customer_id),
        }
        if invoice.subscription_id:
            payload["subscription_id"] = str(invoice.subscription_id)

        OutboxEvent.objects.create(event_type="payment.processed", payload=payload)
        return invoice


class CreateManualInvoiceCommand:
    """
    Creates a standalone (avulsa) invoice for a customer and schedules Asaas charge registration.

    Views are responsible only for input validation; all business logic lives here.
    Both dependencies are injected for testability (DIP).
    """

    def __init__(
        self,
        invoice_repository: AbstractInvoiceWriteRepository,
        customer_repository,  # AbstractCustomerRepository — typed loosely to avoid circular import
    ) -> None:
        self._invoices = invoice_repository
        self._customers = customer_repository

    def execute(
        self,
        *,
        customer_id: str,
        invoice_type: str,
        billing_type: str,
        amount: str,
        due_date: datetime.date,
        description: str = "",
    ) -> Invoice:
        customer = self._customers.get_by_id(UUID(customer_id))
        invoice = self._invoices.create(
            {
                "customer": customer,
                "invoice_type": invoice_type,
                "billing_type": billing_type,
                "description": description,
                "amount": amount,
                "due_date": due_date,
            }
        )

        from apps.billing.tasks import register_charge_task

        register_charge_task.delay(str(invoice.id), billing_type)
        return invoice


class MarkOverdueCommand:
    """
    Marks an invoice as OVERDUE. Called by the daily scheduled scan task.

    Idempotent: repeated calls on an already-OVERDUE invoice are safe no-ops.
    """

    def __init__(self, invoice_id: UUID) -> None:
        self._invoice_id = invoice_id

    @transaction.atomic
    def execute(self) -> Invoice:
        try:
            invoice = Invoice.objects.select_for_update(skip_locked=True).get(pk=self._invoice_id)
        except Invoice.DoesNotExist as exc:
            raise NotFound(f"Invoice {self._invoice_id} não encontrada.") from exc

        if invoice.status == Invoice.Status.OVERDUE:
            return invoice  # Idempotent

        invoice.status = Invoice.Status.OVERDUE
        invoice.save()
        OutboxEvent.objects.create(
            event_type="payment.failed",
            payload={
                "invoice_id": str(invoice.id),
                "customer_id": str(invoice.customer_id),
            },
        )
        return invoice
