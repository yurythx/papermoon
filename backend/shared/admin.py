from django.contrib import admin

from shared.models import OutboxEvent


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "processed",
        "retry_count",
        "created_at",
        "processed_at",
        "failed_at",
    )
    list_filter = ("processed", "event_type")
    search_fields = ("event_type",)
    readonly_fields = ("id", "created_at", "processed_at", "failed_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
