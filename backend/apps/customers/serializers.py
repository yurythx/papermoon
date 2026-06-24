import re

from rest_framework import serializers

from apps.customers.models import Customer, CustomerProfile, Invitation


def _validate_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        raise serializers.ValidationError("CNPJ deve conter 14 dígitos.")
    if digits == digits[0] * 14:
        raise serializers.ValidationError("CNPJ inválido.")

    def _check(d: str, weights: list[int]) -> int:
        total = sum(int(d[i]) * weights[i] for i in range(len(weights)))
        r = total % 11
        return 0 if r < 2 else 11 - r

    if _check(digits, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]) != int(digits[12]):
        raise serializers.ValidationError("CNPJ inválido.")
    if _check(digits, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]) != int(digits[13]):
        raise serializers.ValidationError("CNPJ inválido.")

    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id",
            "company_name",
            "document",
            "status",
            "asaas_customer_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "asaas_customer_id", "created_at", "updated_at")

    def validate_document(self, value: str) -> str:
        return _validate_cnpj(value)


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ("id", "user", "customer", "role")
        read_only_fields = ("id",)


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = (
            "id",
            "email",
            "role",
            "status",
            "expires_at",
            "created_at",
            "accepted_at",
        )
        read_only_fields = ("id", "status", "expires_at", "created_at", "accepted_at")


class CreateInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=CustomerProfile.Role.choices,
        default=CustomerProfile.Role.MEMBER,
    )


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)
