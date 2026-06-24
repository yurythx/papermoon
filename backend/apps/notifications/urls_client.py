from django.urls import path

from apps.notifications.views import (
    InAppNotificationListView,
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
)

urlpatterns = [
    path("", InAppNotificationListView.as_view(), name="client-notifications"),
    path("read-all/", MarkAllNotificationsReadView.as_view(), name="client-notifications-read-all"),
    path("<uuid:pk>/read/", MarkNotificationReadView.as_view(), name="client-notification-read"),
]
