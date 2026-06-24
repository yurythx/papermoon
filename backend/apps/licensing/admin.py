from django.contrib import admin

from apps.licensing.models import ApiKey, LicenseQuota


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ("customer", "key_preview", "is_active", "created_at", "revoked_at")
    list_filter = ("is_active",)
    search_fields = ("customer__company_name",)
    readonly_fields = ("id", "key", "created_at")
    ordering = ("-created_at",)

    def key_preview(self, obj):
        return f"{obj.key[:8]}…"

    key_preview.short_description = "Key"


@admin.register(LicenseQuota)
class LicenseQuotaAdmin(admin.ModelAdmin):
    list_display = ("customer", "used_api_calls", "max_api_calls", "reset_at")
    search_fields = ("customer__company_name",)
    readonly_fields = ("customer",)
