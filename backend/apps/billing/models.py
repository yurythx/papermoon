from uuid import uuid4

from django.db import models
from django.utils import timezone

from shared.models import SoftDeleteManager


class Invoice(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        OVERDUE = "overdue", "Vencido"
        CANCELLED = "cancelled", "Cancelado"

    class Type(models.TextChoices):
        SUBSCRIPTION = "subscription", "Assinatura"
        IMPLEMENTATION = "implementation", "Implantação"
        SUPPORT = "support", "Suporte"

    class BillingType(models.TextChoices):
        BOLETO = "BOLETO", "Boleto"
        PIX = "PIX", "Pix"
        CREDIT_CARD = "CREDIT_CARD", "Cartão de crédito"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices",
    )
    invoice_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SUBSCRIPTION,
        db_index=True,
    )
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateField()
    billing_type = models.CharField(
        max_length=20,
        choices=BillingType.choices,
        default=BillingType.BOLETO,
    )
    asaas_id = models.CharField(max_length=100, blank=True, db_index=True)
    payment_url = models.CharField(max_length=500, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "billing_invoices"
        indexes = [
            models.Index(fields=["status", "due_date"]),
        ]

    def __str__(self) -> str:
        return f"Invoice({self.id} {self.status} {self.amount})"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class WebhookEvent(models.Model):
    """Idempotency guard for Asaas webhook deliveries.

    Asaas may deliver the same event multiple times on transient failures.
    Recording the event id here prevents double-processing (e.g. marking an
    invoice as paid twice).
    """

    asaas_event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "billing_webhook_events"

    def __str__(self) -> str:
        return f"WebhookEvent({self.asaas_event_id} {self.event_type})"
