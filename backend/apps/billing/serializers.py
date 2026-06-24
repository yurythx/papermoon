from rest_framework import serializers

from apps.billing.models import Invoice
from shared.public_urls import sanitize_payment_url


class InvoiceSerializer(serializers.ModelSerializer):
    payment_url = serializers.SerializerMethodField()

    def get_payment_url(self, obj: Invoice) -> str | None:
        return sanitize_payment_url(obj.payment_url)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "customer",
            "invoice_type",
            "description",
            "amount",
            "status",
            "due_date",
            "asaas_id",
            "payment_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "asaas_id", "payment_url", "created_at", "updated_at")
