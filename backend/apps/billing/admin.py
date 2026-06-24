from django.contrib import admin

from apps.billing.models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "invoice_type",
        "amount",
        "status",
        "due_date",
        "asaas_id",
        "created_at",
    )
    list_filter = ("status", "invoice_type")
    search_fields = ("customer__company_name", "asaas_id", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "due_date"
