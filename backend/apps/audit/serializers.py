from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "action",
            "resource_type",
            "resource_id",
            "changes",
            "ip_address",
            "created_at",
            "user_email",
        )

    def get_user_email(self, obj) -> str | None:
        return obj.user.email if obj.user else None
