from datetime import timedelta
import logging
from uuid import UUID

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def handle_asaas_payment_received(self, invoice_id: str) -> None:
    """
    Processes a PAYMENT_RECEIVED event from Asaas.
    Runs asynchronously so the webhook endpoint can return 200 immediately.
    Retries up to 5 times with 60-second delays on transient failures.
    """
    from apps.billing.commands import ConfirmPaymentCommand

    try:
        ConfirmPaymentCommand(UUID(invoice_id)).execute()
    except Exception as exc:
        logger.error("handle_asaas_payment_received failed invoice_id=%s error=%s", invoice_id, exc)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def handle_asaas_payment_overdue(self, invoice_id: str) -> None:
    """
    Processes PAYMENT_OVERDUE / PAYMENT_DELETED events from Asaas.
    Runs asynchronously so the webhook endpoint can return 200 immediately.
    """
    from apps.billing.commands import MarkOverdueCommand

    try:
        MarkOverdueCommand(UUID(invoice_id)).execute()
    except Exception as exc:
        logger.error("handle_asaas_payment_overdue failed invoice_id=%s error=%s", invoice_id, exc)
        raise self.retry(exc=exc) from exc


_DUE_SOON_DAYS = 3


@shared_task
def scan_upcoming_invoices() -> None:
    """Emits payment.due_soon OutboxEvents for invoices due in exactly DUE_SOON_DAYS days.

    Runs daily. The OutboxEvent is processed by the notification consumer, which
    sends an email and an in-app alert to the customer owner.
    """
    from django.db import transaction

    from apps.billing.models import Invoice
    from shared.models import OutboxEvent

    target_date = timezone.localdate() + timedelta(days=_DUE_SOON_DAYS)
    invoices = list(
        Invoice.objects.filter(
            status=Invoice.Status.PENDING,
            due_date=target_date,
        ).values("id", "customer_id", "amount", "due_date")
    )

    for inv in invoices:
        try:
            with transaction.atomic():
                OutboxEvent.objects.create(
                    event_type="payment.due_soon",
                    payload={
                        "invoice_id": str(inv["id"]),
                        "customer_id": str(inv["customer_id"]),
                        "amount": str(inv["amount"]),
                        "due_date": inv["due_date"].isoformat(),
                        "days_until_due": _DUE_SOON_DAYS,
                    },
                )
        except Exception as exc:
            logger.error("scan_upcoming_invoices error invoice_id=%s error=%s", inv["id"], exc)


@shared_task(bind=True, max_retries=5, default_retry_delay=120)
def register_charge_task(self, invoice_id: str, billing_type: str = "BOLETO") -> None:
    """
    Dispatches a new invoice to Asaas as a charge.

    Called after AdminInvoiceListView creates an avulsa invoice.
    Skipped silently when ASAAS_API_KEY is not configured (dev environment).
    """
    from django.conf import settings

    if not settings.ASAAS_API_KEY:
        logger.info(
            "register_charge_task skipped: ASAAS_API_KEY not configured invoice_id=%s", invoice_id
        )
        return

    from apps.billing.commands import RegisterChargeCommand
    from apps.billing.gateway.asaas_adapter import AsaasGateway

    try:
        RegisterChargeCommand(
            invoice_id=UUID(invoice_id),
            gateway=AsaasGateway(),
        ).execute()
    except Exception as exc:
        logger.error("register_charge_task failed invoice_id=%s error=%s", invoice_id, exc)
        raise self.retry(exc=exc) from exc


@shared_task
def scan_overdue_invoices() -> None:
    from apps.billing.commands import MarkOverdueCommand
    from apps.billing.models import Invoice

    today = timezone.localdate()
    overdue_ids = list(
        Invoice.objects.filter(
            status=Invoice.Status.PENDING,
            due_date__lt=today,
        ).values_list("id", flat=True)
    )

    for invoice_id in overdue_ids:
        try:
            # MarkOverdueCommand creates a payment.failed OutboxEvent;
            # notifications app picks it up and sends the overdue email.
            MarkOverdueCommand(invoice_id).execute()
        except Exception as exc:
            logger.error("scan_overdue_invoices error invoice_id=%s error=%s", invoice_id, exc)


_DUNNING_D3 = 3
_DUNNING_D7 = 7


@shared_task
def process_dunning() -> None:
    """
    Progressive dunning for overdue invoices.

    D+3: emits payment.dunning_d3 OutboxEvent → sends a stronger reminder email.
    D+7: suspends the linked subscription if not yet paid.

    Idempotency:
    - D+3 reminder: checked via existing OutboxEvent to avoid duplicate emails.
    - D+7 suspension: SuspendSubscriptionCommand is a no-op if already suspended.
    """
    from django.db import transaction

    from apps.billing.models import Invoice
    from shared.models import OutboxEvent

    today = timezone.localdate()

    # ── D+3 reminder ────────────────────────────────────────────────────────
    d3_cutoff = today - timedelta(days=_DUNNING_D3)
    d3_invoices = list(
        Invoice.objects.filter(
            status=Invoice.Status.OVERDUE,
            due_date__lte=d3_cutoff,
        ).values("id", "customer_id", "subscription_id", "amount", "due_date")
    )

    for inv in d3_invoices:
        already_sent = OutboxEvent.objects.filter(
            event_type="payment.dunning_d3",
            payload__invoice_id=str(inv["id"]),
        ).exists()
        if already_sent:
            continue
        try:
            with transaction.atomic():
                OutboxEvent.objects.create(
                    event_type="payment.dunning_d3",
                    payload={
                        "invoice_id": str(inv["id"]),
                        "customer_id": str(inv["customer_id"]),
                        "amount": str(inv["amount"]),
                        "due_date": inv["due_date"].isoformat(),
                        "days_overdue": (today - inv["due_date"]).days,
                    },
                )
        except Exception as exc:
            logger.error("dunning D+3 error invoice_id=%s error=%s", inv["id"], exc)

    # ── D+7 suspension ───────────────────────────────────────────────────────
    d7_cutoff = today - timedelta(days=_DUNNING_D7)
    d7_invoices = list(
        Invoice.objects.filter(
            status=Invoice.Status.OVERDUE,
            due_date__lte=d7_cutoff,
            subscription_id__isnull=False,
        ).values("id", "customer_id", "subscription_id")
    )

    for d7_inv in d7_invoices:
        try:
            from apps.subscriptions.commands import SuspendSubscriptionCommand

            SuspendSubscriptionCommand().execute(
                subscription_id=d7_inv["subscription_id"],
                reason="dunning_d7_overdue",
            )
            logger.info(
                "dunning D+7 suspended subscription_id=%s invoice_id=%s",
                d7_inv["subscription_id"],
                d7_inv["id"],
            )
        except Exception as exc:
            logger.error("dunning D+7 error invoice_id=%s error=%s", d7_inv["id"], exc)
