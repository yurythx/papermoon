from django.utils import timezone
from rest_framework import serializers

from apps.subscriptions.models import License, ServiceAccess, Subscription
from shared.public_urls import sanitize_public_url


class ServiceAccessSerializer(serializers.ModelSerializer):
    service_url = serializers.SerializerMethodField()

    def get_service_url(self, obj: "ServiceAccess") -> str | None:
        from django.conf import settings

        mapping: dict[str, str | None] = {
            "chatwoot": getattr(settings, "CHATWOOT_API_URL", "") or None,
            "n8n": getattr(settings, "N8N_API_URL", "") or None,
            "glpi": getattr(settings, "GLPI_API_URL", "") or None,
            "zabbix": getattr(settings, "ZABBIX_API_URL", "") or None,
        }
        return sanitize_public_url(mapping.get(obj.service_key), allow_localhost=True)

    class Meta:
        model = ServiceAccess
        fields = [
            "id",
            "license_id",
            "service_key",
            "status",
            "external_id",
            "config",
            "service_url",
            "provisioned_at",
            "suspended_at",
            "error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "license_id", "created_at", "updated_at"]


class LicenseSerializer(serializers.ModelSerializer):
    service_accesses = ServiceAccessSerializer(many=True, read_only=True)

    class Meta:
        model = License
        fields = [
            "id",
            "key",
            "status",
            "valid_from",
            "valid_until",
            "created_at",
            "service_accesses",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    license = LicenseSerializer(read_only=True)
    product_id = serializers.UUIDField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    pricing_id = serializers.UUIDField(source="pricing.id", read_only=True)
    billing_cycle = serializers.CharField(source="pricing.billing_cycle", read_only=True)
    amount = serializers.DecimalField(
        source="pricing.amount", max_digits=10, decimal_places=2, read_only=True
    )
    customer_id = serializers.UUIDField(source="customer.id", read_only=True)
    customer_name = serializers.CharField(source="customer.company_name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "status",
            "customer_id",
            "customer_name",
            "product_id",
            "product_name",
            "product_slug",
            "pricing_id",
            "billing_cycle",
            "amount",
            "starts_at",
            "expires_at",
            "created_at",
            "updated_at",
            "license",
        ]


class LicenseClientSerializer(serializers.ModelSerializer):
    """
    Rich representation for the client-facing /client/licenses/ endpoints.

    Differs from LicenseSerializer (used inside SubscriptionSerializer) by:
    - Adding product context so the client doesn't need a second request
    - Adding days_remaining so the frontend doesn't compute time diffs
    - Renaming service_accesses → services for cleaner API vocabulary
    - Hiding internal fields (revoked_at) that are irrelevant to the client
    """

    product_name = serializers.CharField(source="subscription.product.name", read_only=True)
    product_slug = serializers.CharField(source="subscription.product.slug", read_only=True)
    subscription_id = serializers.UUIDField(source="subscription.id", read_only=True)
    subscription_status = serializers.CharField(source="subscription.status", read_only=True)
    billing_cycle = serializers.CharField(
        source="subscription.pricing.billing_cycle", read_only=True
    )
    amount = serializers.DecimalField(
        source="subscription.pricing.amount",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    services = ServiceAccessSerializer(source="service_accesses", many=True, read_only=True)
    days_remaining = serializers.SerializerMethodField()

    def get_days_remaining(self, obj: License) -> int:
        delta = obj.valid_until - timezone.now()
        return max(0, delta.days)

    class Meta:
        model = License
        fields = [
            "id",
            "key",
            "status",
            "valid_from",
            "valid_until",
            "days_remaining",
            "product_name",
            "product_slug",
            "subscription_id",
            "subscription_status",
            "billing_cycle",
            "amount",
            "services",
            "created_at",
        ]


class CreateSubscriptionSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    pricing_id = serializers.UUIDField()
