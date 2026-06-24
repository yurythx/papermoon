from uuid import uuid4

from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "E-mail"
        WEBHOOK = "webhook", "Webhook"
        IN_APP = "in_app", "In-App"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    # Links to the OutboxEvent that triggered this notification — used for idempotency.
    outbox_event_id = models.UUIDField(null=True, blank=True, db_index=True)
    event_type = models.CharField(max_length=255, db_index=True)
    channel = models.CharField(max_length=50, choices=Channel.choices, db_index=True)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    error = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        constraints = [
            # One notification per (outbox_event, channel) — prevents duplicate sends on retry.
            models.UniqueConstraint(
                fields=["outbox_event_id", "channel"],
                condition=models.Q(outbox_event_id__isnull=False),
                name="unique_notification_per_outbox_event_channel",
            )
        ]

    def __str__(self) -> str:
        return f"{self.event_type} → {self.channel}:{self.recipient} [{self.status}]"
