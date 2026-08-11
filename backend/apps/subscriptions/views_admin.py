from drf_spectacular.utils import OpenApiParameter, extend_schema
import requests
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.utils import log_action
from apps.provisioning.keycloak import (
    KeycloakClientAlreadyExistsError,
    KeycloakConnectionUnavailableError,
)
from apps.subscriptions.commands import (
    CancelSubscriptionCommand,
    ChangeSubscriptionPlanCommand,
    CreateSubscriptionCommand,
    RenewSubscriptionCommand,
    SuspendSubscriptionCommand,
)
from apps.subscriptions.keycloak_guide import (
    KeycloakNoServiceAccessError,
    build_integration_guide,
    create_client_integration,
    keycloak_integrations_queryset,
    resolve_endpoints,
    resolve_keycloak_context,
    serialize_keycloak_integration,
    validate_language_and_base_url,
)
from apps.subscriptions.keycloak_integration_content import LANGUAGE_PACKS
from apps.subscriptions.models import Subscription
from apps.subscriptions.serializers import CreateSubscriptionSerializer, SubscriptionSerializer
from shared.schemas import (
    ChangePlanRequestSerializer,
    KeycloakIntegrationCreateRequestSerializer,
    KeycloakIntegrationCreateResponseSerializer,
    KeycloakIntegrationGuideResponseSerializer,
    KeycloakIntegrationListResponseSerializer,
    KeycloakIntegrationSecretResponseSerializer,
    KeycloakIssuerValidateRequestSerializer,
    KeycloakIssuerValidateResponseSerializer,
    SuspendReasonRequestSerializer,
)
from shared.throttling import (
    AdminWriteThrottle,
    KeycloakClientCreateRateThrottle,
    KeycloakConnectionTestRateThrottle,
)


@extend_schema(tags=["Admin — Subscriptions"])
class AdminSubscriptionListCreateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="admin_subscriptions_list",
        summary="Listar assinaturas",
        parameters=[
            OpenApiParameter("customer_id", str, description="Filtrar por customer UUID"),
            OpenApiParameter(
                "search", str, description="Busca por razão social do cliente (icontains)"
            ),
            OpenApiParameter(
                "status",
                str,
                description="trial | active | grace_period | suspended | expired | cancelled",
            ),
            OpenApiParameter(
                "ordering", str, description="-created_at | created_at | expires_at | -expires_at"
            ),
            OpenApiParameter("page", int),
        ],
        responses={200: SubscriptionSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        from rest_framework.pagination import PageNumberPagination

        from apps.subscriptions.queries import list_subscriptions_admin

        qs = list_subscriptions_admin(
            customer_id=request.query_params.get("customer_id") or None,
            search=request.query_params.get("search") or None,
            status=request.query_params.get("status") or None,
            ordering=request.query_params.get("ordering", "-created_at"),
        )
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(SubscriptionSerializer(page, many=True).data)

    @extend_schema(
        summary="Criar assinatura manualmente",
        request=CreateSubscriptionSerializer,
        responses={201: SubscriptionSerializer},
    )
    def post(self, request: Request) -> Response:
        ser = CreateSubscriptionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        subscription = CreateSubscriptionCommand().execute(
            customer_id=ser.validated_data["customer_id"],
            product_id=ser.validated_data["product_id"],
            pricing_id=ser.validated_data["pricing_id"],
        )
        return Response(SubscriptionSerializer(subscription).data, status=201)


@extend_schema(tags=["Admin — Subscriptions"])
class AdminSubscriptionDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get(self, pk: str) -> Subscription:
        from apps.subscriptions.queries import get_subscription_by_id

        return get_subscription_by_id(pk)

    @extend_schema(summary="Detalhe de uma assinatura", responses={200: SubscriptionSerializer})
    def get(self, request: Request, pk: str) -> Response:
        return Response(SubscriptionSerializer(self._get(pk)).data)


@extend_schema(tags=["Admin — Subscriptions"])
class AdminSubscriptionSuspendView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Suspender assinatura",
        request=SuspendReasonRequestSerializer,
        responses={200: SubscriptionSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        reason = request.data.get("reason", "")
        subscription = SuspendSubscriptionCommand().execute(pk, reason=reason)
        return Response(SubscriptionSerializer(subscription).data)


@extend_schema(tags=["Admin — Subscriptions"])
class AdminSubscriptionRenewView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Renovar assinatura", request=None, responses={200: SubscriptionSerializer}
    )
    def post(self, request: Request, pk: str) -> Response:
        subscription = RenewSubscriptionCommand().execute(pk)
        return Response(SubscriptionSerializer(subscription).data)


@extend_schema(tags=["Admin — Subscriptions"])
class AdminSubscriptionCancelView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Cancelar assinatura",
        request=SuspendReasonRequestSerializer,
        responses={200: SubscriptionSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        reason = request.data.get("reason", "")
        subscription = CancelSubscriptionCommand().execute(pk, reason=reason)
        return Response(SubscriptionSerializer(subscription).data)


@extend_schema(tags=["Admin — Subscriptions"])
class AdminSubscriptionChangePlanView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Mudar plano de uma assinatura (upgrade/downgrade)",
        request=ChangePlanRequestSerializer,
        responses={201: SubscriptionSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        new_pricing_id = request.data.get("pricing_id")
        if not new_pricing_id:
            raise ValidationError({"pricing_id": "This field is required."})
        try:
            new_sub = ChangeSubscriptionPlanCommand().execute(pk, new_pricing_id)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        log_action(
            "subscription.plan_changed",
            "Subscription",
            str(new_sub.id),
            user=request.user,
            changes={"pricing_id": new_pricing_id},
            request=request,
        )
        return Response(SubscriptionSerializer(new_sub).data, status=201)


# ---------------------------------------------------------------------------
# Keycloak — ferramentas de suporte pro staff (backoffice)
#
# Duas coisas diferentes:
#  1. AdminKeycloak*View (guide/list-create/secret): staff escolhe um cliente
#     (customer_id na URL) e opera a MESMA funcionalidade da página do
#     cliente — gera guia e cria integrações de verdade em nome dele, pra
#     ajudar com o suporte. Reaproveita 100% da lógica de
#     apps.subscriptions.keycloak_guide (a mesma usada pelo cliente).
#  2. AdminKeycloakIssuerValidatorView: ferramenta genérica, sem vínculo com
#     nenhum cliente — só valida discovery/conectividade de um issuer
#     qualquer, útil pra diagnosticar um Keycloak externo antes de mais nada.
# ---------------------------------------------------------------------------


def _get_customer_or_404(customer_id: str):
    from django.shortcuts import get_object_or_404

    from apps.customers.models import Customer

    return get_object_or_404(Customer, pk=customer_id)


# Diferente do padrão client-facing (mensagem genérica, esconde o motivo):
# aqui é o próprio staff tentando resolver o problema, então expor o motivo
# exato é o ponto — não tem "cliente" pra proteger dessa informação.
_PLATFORM_NOT_CONFIGURED_STAFF_MESSAGE = (
    "A conexão central do PaperMoon com o Keycloak não está configurada/ativa. "
    "Configure em Configurações → Conexão com o Keycloak (provisionamento) antes de continuar."
)


def _no_service_access_staff_message(customer) -> str:
    return (
        f"{customer.company_name} não tem um serviço 'keycloak' ativo (realm provisionado) "
        "— verifique a assinatura/provisionamento antes de criar uma integração."
    )


@extend_schema(tags=["Admin — Keycloak"])
class AdminKeycloakIntegrationGuideView(APIView):
    """Mesmo guia read-only de ClientKeycloakIntegrationGuideView, mas em
    nome de um cliente escolhido pelo staff (customer_id na URL) — ferramenta
    de suporte, não exige logar como o cliente pra ver como a integração dele
    ficaria."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="admin_keycloak_integration_guide",
        summary="Gerar guia de integração Keycloak em nome de um cliente",
        parameters=[
            OpenApiParameter(
                "language", str, OpenApiParameter.QUERY, required=True, enum=list(LANGUAGE_PACKS)
            ),
            OpenApiParameter("app_name", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("base_url", str, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("redirect_path", str, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: KeycloakIntegrationGuideResponseSerializer},
    )
    def get(self, request: Request, customer_id: str) -> Response:
        customer = _get_customer_or_404(customer_id)
        language, base_url = validate_language_and_base_url(
            request.query_params.get("language", ""),
            request.query_params.get("base_url", "").strip(),
        )
        app_name = request.query_params.get("app_name", "").strip() or "minha-aplicacao"
        redirect_path = request.query_params.get("redirect_path", "").strip() or None

        guide = build_integration_guide(
            customer,
            language=language,
            app_name=app_name,
            base_url=base_url,
            redirect_path=redirect_path,
        )
        return Response(guide)


@extend_schema(tags=["Admin — Keycloak"])
class AdminKeycloakIntegrationListCreateView(APIView):
    """Mesma funcionalidade de ClientKeycloakIntegrationListCreateView, mas
    operando em nome de um cliente escolhido pelo staff (customer_id na URL).

    Diferente da view do cliente, os erros aqui expõem o motivo exato
    (conexão central vs. acesso do cliente) — é staff tentando resolver o
    problema, esconder a causa não ajudaria ninguém."""

    permission_classes = [IsAdminUser]

    def get_throttles(self) -> list:
        if self.request.method == "POST":
            return [KeycloakClientCreateRateThrottle()]
        return super().get_throttles()

    @extend_schema(
        operation_id="admin_keycloak_integrations_list",
        summary="Listar integrações Keycloak de um cliente",
        responses={200: KeycloakIntegrationListResponseSerializer},
    )
    def get(self, request: Request, customer_id: str) -> Response:
        customer = _get_customer_or_404(customer_id)
        _ctx, reason = resolve_keycloak_context(customer)
        integrations = keycloak_integrations_queryset(customer).order_by("-created_at")
        return Response(
            {
                "available": reason is None,
                "reason": reason,
                "integrations": [serialize_keycloak_integration(i) for i in integrations],
            }
        )

    @extend_schema(
        operation_id="admin_keycloak_integrations_create",
        summary="Criar integração Keycloak em nome de um cliente (client OIDC de verdade)",
        request=KeycloakIntegrationCreateRequestSerializer,
        responses={201: KeycloakIntegrationCreateResponseSerializer},
    )
    def post(self, request: Request, customer_id: str) -> Response:
        customer = _get_customer_or_404(customer_id)

        language, base_url = validate_language_and_base_url(
            (request.data.get("language") or "").strip(),
            (request.data.get("base_url") or "").strip(),
        )
        app_name = (request.data.get("app_name") or "").strip() or "minha-aplicacao"
        redirect_path = (request.data.get("redirect_path") or "").strip() or None

        try:
            result = create_client_integration(
                customer=customer,
                language=language,
                app_name=app_name,
                base_url=base_url,
                redirect_path=redirect_path,
                actor=request.user,
                request=request,
            )
        except KeycloakConnectionUnavailableError:
            return Response(
                {
                    "code": "platform_not_configured",
                    "message": _PLATFORM_NOT_CONFIGURED_STAFF_MESSAGE,
                    "details": [],
                },
                status=409,
            )
        except KeycloakNoServiceAccessError:
            return Response(
                {
                    "code": "no_service_access",
                    "message": _no_service_access_staff_message(customer),
                    "details": [],
                },
                status=403,
            )
        except KeycloakClientAlreadyExistsError:
            return Response(
                {
                    "code": "client_already_exists",
                    "message": (
                        "Já existe uma integração com esse identificador pra esse cliente — "
                        "escolha outro nome de aplicação."
                    ),
                    "details": [],
                },
                status=409,
            )
        except requests.RequestException as exc:
            return Response(
                {
                    "code": "keycloak_unreachable",
                    "message": f"Não foi possível conectar ao Keycloak agora: {exc}",
                    "details": [],
                },
                status=502,
            )

        return Response(result, status=201)


@extend_schema(tags=["Admin — Keycloak"])
class AdminKeycloakIntegrationSecretView(APIView):
    """Rebusca o client_secret fresco no Keycloak em nome de um cliente
    escolhido pelo staff — mesmo raciocínio de
    ClientKeycloakIntegrationSecretView, nunca fica persistido localmente."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="admin_keycloak_integration_secret",
        summary="Ver client_secret de uma integração de um cliente",
        responses={200: KeycloakIntegrationSecretResponseSerializer},
    )
    def get(self, request: Request, customer_id: str, pk: str) -> Response:
        from django.shortcuts import get_object_or_404

        from apps.provisioning.keycloak import KeycloakProvisioner

        customer = _get_customer_or_404(customer_id)
        integration = get_object_or_404(keycloak_integrations_queryset(customer), pk=pk)

        if integration.public_client:
            raise ValidationError(
                {"detail": "Este client é público (PKCE) — não tem client_secret."}
            )

        _ctx, reason = resolve_keycloak_context(customer)
        if reason is not None:
            message = (
                _PLATFORM_NOT_CONFIGURED_STAFF_MESSAGE
                if reason == "platform_not_configured"
                else _no_service_access_staff_message(customer)
            )
            status_code = 409 if reason == "platform_not_configured" else 403
            return Response({"code": reason, "message": message, "details": []}, status=status_code)

        provisioner = KeycloakProvisioner()
        try:
            client_secret = provisioner.get_client_secret(
                realm=integration.realm, kc_uuid=integration.kc_uuid
            )
        except KeycloakConnectionUnavailableError:
            return Response(
                {
                    "code": "platform_not_configured",
                    "message": _PLATFORM_NOT_CONFIGURED_STAFF_MESSAGE,
                    "details": [],
                },
                status=409,
            )
        except requests.RequestException as exc:
            return Response(
                {
                    "code": "keycloak_unreachable",
                    "message": f"Não foi possível conectar ao Keycloak agora: {exc}",
                    "details": [],
                },
                status=502,
            )

        log_action(
            "keycloak_client_integration.secret_viewed",
            "KeycloakClientIntegration",
            str(integration.pk),
            user=request.user,
            request=request,
            changes={"client_id": integration.client_id, "customer_id": str(customer.id)},
        )
        return Response({"client_secret": client_secret})


@extend_schema(tags=["Admin — Keycloak"])
class AdminKeycloakIssuerValidatorView(APIView):
    """Ferramenta de diagnóstico genérica — confirma o discovery document de
    QUALQUER issuer (não precisa ser um cliente/realm do PaperMoon). Útil pra
    validar o Keycloak de um cliente externo antes de ajudar com a integração
    dele, sem precisar ter nada configurado/provisionado ainda."""

    permission_classes = [IsAdminUser]
    throttle_classes = [KeycloakConnectionTestRateThrottle]

    @extend_schema(
        operation_id="admin_keycloak_validate_issuer",
        summary="Validar um issuer/URL do Keycloak (diagnóstico, sem vínculo com cliente)",
        request=KeycloakIssuerValidateRequestSerializer,
        responses={200: KeycloakIssuerValidateResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        issuer = (request.data.get("issuer") or "").strip().rstrip("/")
        if not issuer.startswith(("http://", "https://")):
            raise ValidationError({"issuer": "Informe uma URL http(s) completa."})

        endpoints, verified = resolve_endpoints(issuer)
        return Response(
            {
                "verified": verified,
                "issuer": issuer,
                "authorization_endpoint": endpoints["authorization_endpoint"],
                "token_endpoint": endpoints["token_endpoint"],
                "userinfo_endpoint": endpoints["userinfo_endpoint"],
                "jwks_uri": endpoints["jwks_uri"],
                "end_session_endpoint": endpoints["end_session_endpoint"],
            }
        )
