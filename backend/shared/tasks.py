from datetime import timedelta
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_outbox_events() -> None:
    from shared.models import OutboxEvent

    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = OutboxEvent.objects.filter(processed=True, processed_at__lt=cutoff).delete()
    logger.info("cleanup_old_outbox_events deleted=%d", deleted)
