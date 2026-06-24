from django.db.models import QuerySet

from apps.notifications.models import Notification


def list_in_app_notifications(customer_id: str) -> QuerySet:
    """All in-app notifications for a customer, newest first."""
    return Notification.objects.filter(
        channel=Notification.Channel.IN_APP,
        recipient=customer_id,
    ).order_by("-created_at")
