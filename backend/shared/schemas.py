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
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
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
    feature_flags = serializers.ListField(child=serializers.CharField())


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


class KeycloakIntegrationGuideResponseSerializer(serializers.Serializer):
    """Só para o schema OpenAPI/drf-spectacular — a view monta a Response à
    mão a partir de apps.subscriptions.keycloak_guide.build_integration_guide().
    """

    available = serializers.BooleanField()
    verified = serializers.BooleanField(required=False)
    issuer = serializers.CharField(required=False)
    authorization_endpoint = serializers.CharField(required=False)
    token_endpoint = serializers.CharField(required=False)
    userinfo_endpoint = serializers.CharField(required=False)
    jwks_uri = serializers.CharField(required=False)
    end_session_endpoint = serializers.CharField(required=False)
    client_id_suggestion = serializers.CharField(required=False)
    redirect_uri = serializers.CharField(required=False)
    scopes = serializers.ListField(child=serializers.CharField(), required=False)
    language = serializers.CharField(required=False)
    package = serializers.CharField(required=False)
    install_command = serializers.CharField(required=False)
    steps = serializers.ListField(child=serializers.CharField(), required=False)
    code_snippet = serializers.CharField(required=False)


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


class SSOCallbackRequestSerializer(serializers.Serializer):
    code = serializers.CharField(help_text="Authorization code retornado pelo Keycloak.")
    state = serializers.CharField(help_text="state gerado por /auth/sso/login/.")


class TokenPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class AuthorizeUrlResponseSerializer(serializers.Serializer):
    authorize_url = serializers.URLField()


class SSOStatusResponseSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()


class SSOConfigResponseSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    issuer = serializers.CharField(allow_blank=True)
    client_id = serializers.CharField(allow_blank=True)
    client_secret_set = serializers.BooleanField()
    staff_group = serializers.CharField(allow_blank=True)
    redirect_uri = serializers.CharField()
    updated_at = serializers.DateTimeField(allow_null=True)
    updated_by_email = serializers.EmailField(allow_null=True)


class SSOConfigUpdateRequestSerializer(serializers.Serializer):
    """
    PATCH parcial de verdade: `issuer`/`client_id`/`client_secret` ausentes do body
    mantêm o valor já salvo (sem `default=""` — um campo ausente não aparece em
    `validated_data`, então a view consegue distinguir "omitido" de "enviado em
    branco"). A validação de "enabled exige issuer/client_id/secret" fica na view,
    que é quem tem acesso ao valor já salvo no banco para fazer o fallback.
    """

    enabled = serializers.BooleanField()
    issuer = serializers.CharField(required=False, allow_blank=True)
    client_id = serializers.CharField(required=False, allow_blank=True)
    client_secret = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Omitido (ou em branco) mantém o segredo já salvo.",
    )
    staff_group = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            "Grupo do Keycloak (claim 'groups') que autoriza criar conta staff "
            "automaticamente no primeiro login. Em branco desativa o JIT."
        ),
    )


class SSOTestRequestSerializer(serializers.Serializer):
    issuer = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Se omitido, testa o issuer já salvo.",
    )


class SSOTestResponseSerializer(serializers.Serializer):
    reachable = serializers.BooleanField()
    message = serializers.CharField()


class KeycloakConnectionResponseSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    api_url = serializers.CharField(allow_blank=True)
    admin_token_set = serializers.BooleanField()
    updated_at = serializers.DateTimeField(allow_null=True)
    updated_by_email = serializers.EmailField(allow_null=True)


class KeycloakConnectionUpdateRequestSerializer(serializers.Serializer):
    """
    PATCH parcial de verdade, mesmo padrão de SSOConfigUpdateRequestSerializer:
    `api_url`/`admin_token` ausentes do body mantêm o valor já salvo.
    """

    enabled = serializers.BooleanField()
    api_url = serializers.CharField(required=False, allow_blank=True)
    admin_token = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Omitido (ou em branco) mantém o admin_token já salvo.",
    )


class KeycloakConnectionTestRequestSerializer(serializers.Serializer):
    api_url = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Se omitido, testa a api_url já salva.",
    )
    admin_token = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Se omitido, testa o admin_token já salvo.",
    )


class KeycloakConnectionTestResponseSerializer(serializers.Serializer):
    reachable = serializers.BooleanField()
    message = serializers.CharField()


class KeycloakClientIntegrationSerializer(serializers.Serializer):
    """Item de `GET .../keycloak-integrations/` — nunca inclui client_secret,
    que só é servido sob demanda por KeycloakClientIntegrationSecretView."""

    id = serializers.UUIDField()
    client_id = serializers.CharField()
    realm = serializers.CharField()
    app_name = serializers.CharField()
    base_url = serializers.CharField()
    redirect_uri = serializers.CharField()
    language = serializers.CharField()
    public_client = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class KeycloakIntegrationListResponseSerializer(serializers.Serializer):
    available = serializers.BooleanField()
    reason = serializers.CharField(allow_null=True)
    integrations = KeycloakClientIntegrationSerializer(many=True)


class KeycloakIntegrationCreateRequestSerializer(serializers.Serializer):
    language = serializers.CharField()
    app_name = serializers.CharField(required=False, allow_blank=True)
    base_url = serializers.CharField()
    redirect_path = serializers.CharField(required=False, allow_blank=True)


class KeycloakIntegrationCreateResponseSerializer(serializers.Serializer):
    """Igual a KeycloakIntegrationGuideResponseSerializer, mais os campos do
    client criado de verdade — client_secret só aparece aqui, uma vez, na
    criação (e de novo sob demanda em .../secret/); nunca fica persistido."""

    id = serializers.UUIDField()
    client_id = serializers.CharField()
    client_secret = serializers.CharField(allow_null=True)
    public_client = serializers.BooleanField()
    verified = serializers.BooleanField()
    issuer = serializers.CharField()
    authorization_endpoint = serializers.CharField()
    token_endpoint = serializers.CharField()
    userinfo_endpoint = serializers.CharField()
    jwks_uri = serializers.CharField()
    end_session_endpoint = serializers.CharField()
    redirect_uri = serializers.CharField()
    scopes = serializers.ListField(child=serializers.CharField())
    language = serializers.CharField()
    package = serializers.CharField()
    install_command = serializers.CharField()
    steps = serializers.ListField(child=serializers.CharField())
    code_snippet = serializers.CharField()


class KeycloakIntegrationSecretResponseSerializer(serializers.Serializer):
    client_secret = serializers.CharField()


class KeycloakIssuerValidateRequestSerializer(serializers.Serializer):
    """Ferramenta de diagnóstico do staff (Admin — Keycloak): confirma o
    discovery document de QUALQUER issuer, sem vincular a um cliente/realm
    específico do PaperMoon — útil pra validar o Keycloak de um cliente
    externo antes de ajudar com a integração dele."""

    issuer = serializers.CharField()


class KeycloakIssuerValidateResponseSerializer(serializers.Serializer):
    verified = serializers.BooleanField()
    issuer = serializers.CharField()
    authorization_endpoint = serializers.CharField()
    token_endpoint = serializers.CharField()
    userinfo_endpoint = serializers.CharField()
    jwks_uri = serializers.CharField()
    end_session_endpoint = serializers.CharField()


class KeycloakCodeSnippetRequestSerializer(serializers.Serializer):
    """Gera um exemplo de código de integração pra uma stack, a partir de
    valores informados manualmente — não depende de nenhum cliente/realm do
    PaperMoon, complementa KeycloakIssuerValidateRequestSerializer pro mesmo
    fluxo de suporte a um Keycloak de terceiro (sem Admin API disponível)."""

    language = serializers.CharField()
    issuer = serializers.CharField()
    client_id = serializers.CharField()
    base_url = serializers.CharField()
    redirect_uri = serializers.CharField()


class KeycloakCodeSnippetResponseSerializer(serializers.Serializer):
    language = serializers.CharField()
    public_client = serializers.BooleanField()
    package = serializers.CharField()
    install_command = serializers.CharField()
    steps = serializers.ListField(child=serializers.CharField())
    code_snippet = serializers.CharField()
    verified = serializers.BooleanField()


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
