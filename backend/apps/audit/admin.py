from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "resource_type", "resource_id", "user", "ip_address", "created_at")
    list_filter = ("action", "resource_type")
    search_fields = ("resource_id", "user__email", "action")
    readonly_fields = (
        "id",
        "user",
        "action",
        "resource_type",
        "resource_id",
        "changes",
        "ip_address",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
