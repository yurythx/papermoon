from rest_framework import serializers

from apps.products.models import Pricing, Product, ServiceComponent


class ServiceComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceComponent
        fields = ["id", "service_key", "config"]


class PricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pricing
        fields = [
            "id",
            "billing_cycle",
            "amount",
            "trial_days",
            "max_api_calls",
            "max_users",
            "is_active",
        ]


class ProductSerializer(serializers.ModelSerializer):
    components = ServiceComponentSerializer(many=True, read_only=True)
    pricings = PricingSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "components",
            "pricings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "slug", "description", "is_active"]
