from django.contrib import admin

from apps.products.models import Pricing, Product, ServiceComponent


class ServiceComponentInline(admin.TabularInline):
    model = ServiceComponent
    extra = 0
    fields = ["service_key", "config"]


class PricingInline(admin.TabularInline):
    model = Pricing
    extra = 0
    fields = ["billing_cycle", "amount", "trial_days", "max_users", "max_api_calls", "is_active"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ServiceComponentInline, PricingInline]
    readonly_fields = ["id", "created_at", "updated_at"]
