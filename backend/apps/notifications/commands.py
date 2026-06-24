from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.notifications.models import Notification


class MarkNotificationReadCommand:
    def execute(self, notification_id: UUID | str, customer_id: str) -> Notification:
        try:
            notification = Notification.objects.get(
                pk=notification_id,
                channel=Notification.Channel.IN_APP,
                recipient=customer_id,
            )
        except Notification.DoesNotExist as exc:
            raise NotFound("Notificação não encontrada.") from exc

        if notification.status != Notification.Status.SENT:
            notification.status = Notification.Status.SENT
            notification.sent_at = timezone.now()
            notification.save(update_fields=["status", "sent_at"])

        return notification


class MarkAllNotificationsReadCommand:
    def execute(self, customer_id: str) -> int:
        return Notification.objects.filter(
            channel=Notification.Channel.IN_APP,
            recipient=customer_id,
            status=Notification.Status.PENDING,
        ).update(status=Notification.Status.SENT, sent_at=timezone.now())
