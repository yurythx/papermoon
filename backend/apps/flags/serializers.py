from __future__ import annotations

from rest_framework import serializers

from apps.customers.models import Customer
from apps.flags.models import FeatureFlag


class FeatureFlagCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "company_name")


class FeatureFlagSerializer(serializers.ModelSerializer):
    enabled_customers = FeatureFlagCustomerSerializer(many=True, read_only=True)
    # Escrita separada da leitura — o front manda uma lista de UUIDs, a
    # leitura devolve {id, company_name} pra não precisar de uma segunda
    # chamada só pra mostrar o nome de cada customer selecionado.
    enabled_customer_ids = serializers.PrimaryKeyRelatedField(
        source="enabled_customers",
        queryset=Customer.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = FeatureFlag
        fields = (
            "id",
            "key",
            "name",
            "description",
            "enabled_globally",
            "enabled_customers",
            "enabled_customer_ids",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
