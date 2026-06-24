"""
Reusable response serializers for drf-spectacular @extend_schema(responses=...).

These are pure schema classes — they define the shape of API responses for OpenAPI
documentation. They are not used for deserialization or validation.
"""

from rest_framework import serializers


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class AcceptInviteResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    customer_id = serializers.UUIDField()
    role = serializers.CharField()


class MeUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    username = serializers.CharField()
    is_staff = serializers.BooleanField()


class MeCustomerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    company_name = serializers.CharField()
    document = serializers.CharField()
    status = serializers.CharField()


class MeResponseSerializer(serializers.Serializer):
    user = MeUserSerializer()
    customer = MeCustomerSerializer(allow_null=True)
    role = serializers.CharField(allow_null=True)


class ApiKeyItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    key = serializers.CharField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    revoked_at = serializers.DateTimeField(allow_null=True)


class ApiKeyCreateResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    key = serializers.CharField()
    is_active = serializers.BooleanField()


class ValidateApiKeyResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_null=True)
    quota_remaining = serializers.IntegerField(allow_null=True)


class ValidateLicenseResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    status = serializers.CharField(required=False)
    valid_until = serializers.DateTimeField(required=False)
    product = serializers.CharField(required=False)
    reason = serializers.CharField(required=False, allow_null=True)
    services = serializers.DictField(child=serializers.CharField(), required=False)


class FinancialMetricsSerializer(serializers.Serializer):
    total_paid = serializers.FloatField()
    total_pending = serializers.FloatField()
    total_overdue = serializers.FloatField()


class ApiQuotaSerializer(serializers.Serializer):
    used_api_calls = serializers.IntegerField()
    max_api_calls = serializers.IntegerField()
    reset_at = serializers.DateTimeField(allow_null=True)
    usage_pct = serializers.FloatField()
    plan_name = serializers.CharField(allow_null=True)
    plan_slug = serializers.CharField(allow_null=True)
    billing_cycle = serializers.CharField(allow_null=True)


class TeamMemberItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    username = serializers.CharField()
    role = serializers.CharField()
    joined_at = serializers.DateTimeField()
    is_you = serializers.BooleanField()


class MRRMetricsMonthSerializer(serializers.Serializer):
    month = serializers.CharField()
    revenue = serializers.FloatField()


class RevenueByPlanSerializer(serializers.Serializer):
    plan = serializers.CharField()
    revenue = serializers.FloatField()
    customer_count = serializers.IntegerField()


class MRRMetricsSerializer(serializers.Serializer):
    mrr = serializers.FloatField()
    arr = serializers.FloatField()
    active_customers = serializers.IntegerField(required=False)
    new_customers = serializers.IntegerField(required=False)
    churned_customers = serializers.IntegerField(required=False)
    churn_rate = serializers.FloatField(required=False)
    at_risk_count = serializers.IntegerField(required=False)
    revenue_by_plan = RevenueByPlanSerializer(many=True, required=False)
    monthly_revenue = MRRMetricsMonthSerializer(many=True)


class APIUsageRowSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    company_name = serializers.CharField()
    used_api_calls = serializers.IntegerField()
    max_api_calls = serializers.IntegerField()
    usage_pct = serializers.FloatField()
    reset_at = serializers.DateTimeField()


class AdminInvoiceRowSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    customer_id = serializers.UUIDField()
    company_name = serializers.CharField()
    invoice_type = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.CharField()
    status = serializers.CharField()
    due_date = serializers.DateField()
    asaas_id = serializers.CharField()
    payment_url = serializers.CharField()
    created_at = serializers.DateTimeField()


class NotificationItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    event_type = serializers.CharField()
    subject = serializers.CharField()
    body = serializers.CharField()
    is_read = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    read_at = serializers.DateTimeField(allow_null=True)


# ---------------------------------------------------------------------------
# Request body schemas (used in @extend_schema(request=...))
# ---------------------------------------------------------------------------


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Refresh token JWT a ser invalidado.")


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmRequestSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(min_length=8)


class ChangePasswordRequestSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


class SuspendReasonRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class ChangePlanRequestSerializer(serializers.Serializer):
    pricing_id = serializers.UUIDField(help_text="UUID do novo pricing a ser aplicado.")


class ServiceAccessCreateRequestSerializer(serializers.Serializer):
    service_key = serializers.CharField(help_text="Chave do serviço (ex: chatwoot, n8n, whatsapp).")
    config = serializers.DictField(required=False, default=dict)


class SubscribeRequestSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    pricing_id = serializers.UUIDField()


class ServiceAccessPatchRequestSerializer(serializers.Serializer):
    config = serializers.DictField(required=False)
    external_id = serializers.CharField(required=False, allow_blank=True)
