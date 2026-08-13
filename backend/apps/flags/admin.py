from django.contrib import admin

from apps.flags.models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "enabled_globally", "updated_at")
    list_filter = ("enabled_globally",)
    search_fields = ("key", "name")
    filter_horizontal = ("enabled_customers",)
    readonly_fields = ("created_at", "updated_at")
