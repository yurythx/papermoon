from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "channel", "recipient", "status", "sent_at", "created_at")
    list_filter = ("channel", "status", "event_type")
    search_fields = ("recipient", "subject", "event_type")
    readonly_fields = ("id", "created_at", "sent_at")
    ordering = ("-created_at",)
