from uuid import uuid4

from django.db import models


class SoftDeleteManager(models.Manager):
    """Default manager that excludes soft-deleted records."""

    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True)


class OutboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event_type = models.CharField(max_length=255)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "shared_outbox_events"
        ordering = ["created_at"]
        indexes = [
            # Query padrão do consumer: WHERE processed=False ORDER BY created_at
            models.Index(fields=["processed", "created_at"], name="outbox_pending_idx"),
        ]

    def __str__(self) -> str:
        return f"OutboxEvent({self.event_type} processed={self.processed})"
