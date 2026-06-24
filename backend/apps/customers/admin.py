from django.contrib import admin

from apps.customers.models import Customer, CustomerProfile


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "document",
        "status",
        "asaas_customer_id",
        "deleted_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("company_name", "document", "asaas_customer_id")
    readonly_fields = ("id", "asaas_customer_id", "created_at", "updated_at")
    ordering = ("-created_at",)
    actions = ["mark_suspended", "mark_active"]

    @admin.action(description="Suspender selecionados")
    def mark_suspended(self, request, queryset):
        queryset.update(status=Customer.Status.SUSPENDED)

    @admin.action(description="Reativar selecionados")
    def mark_active(self, request, queryset):
        queryset.update(status=Customer.Status.ACTIVE)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "customer", "role")
    list_filter = ("role",)
    search_fields = ("user__email", "customer__company_name")
