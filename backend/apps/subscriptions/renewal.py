"""
Renewal invoice generation.

Creates an Invoice linked to the Subscription 3 days before expiry,
then dispatches it to Asaas for collection.
The webhook flow closes the loop: Asaas calls back → ConfirmPaymentCommand
→ payment.processed OutboxEvent → renew_subscription_on_payment handler
→ RenewSubscriptionCommand extends expires_at.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from apps.billing.models import Invoice

from django.db import transaction

logger = logging.getLogger(__name__)


class GenerateRenewalInvoiceCommand:
    def execute(self, subscription_id: UUID) -> Invoice | None:
        from apps.billing.models import Invoice
        from apps.subscriptions.models import Subscription
        from shared.models import OutboxEvent

        try:
            sub = Subscription.objects.select_related("customer", "pricing").get(pk=subscription_id)
        except Subscription.DoesNotExist:
            logger.error("GenerateRenewalInvoiceCommand sub not found id=%s", subscription_id)
            return None

        if sub.status not in {
            Subscription.Status.ACTIVE,
            Subscription.Status.TRIAL,
            Subscription.Status.GRACE_PERIOD,
        }:
            return None  # Nothing to renew

        # Idempotent — one pending invoice per subscription per billing cycle
        already_exists = Invoice.objects.filter(
            subscription=sub,
            status=Invoice.Status.PENDING,
        ).exists()
        if already_exists:
            logger.info(
                "GenerateRenewalInvoiceCommand already has pending invoice sub_id=%s",
                subscription_id,
            )
            return None

        with transaction.atomic():
            invoice = Invoice.objects.create(
                customer=sub.customer,
                subscription=sub,
                amount=sub.pricing.amount,
                due_date=sub.expires_at.date(),
                status=Invoice.Status.PENDING,
            )
            OutboxEvent.objects.create(
                event_type="renewal_invoice.created",
                payload={
                    "invoice_id": str(invoice.id),
                    "subscription_id": str(sub.id),
                    "customer_id": str(sub.customer_id),
                    "amount": str(invoice.amount),
                    "due_date": invoice.due_date.isoformat(),
                },
            )

        logger.info(
            "GenerateRenewalInvoiceCommand invoice=%s sub=%s amount=%s",
            invoice.id,
            subscription_id,
            invoice.amount,
        )
        return invoice
