from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import CustomUser
from apps.audit.utils import log_action
from apps.provisioning.keycloak_config import (
    test_admin_connectivity,
    update_keycloak_connection,
)
from apps.provisioning.models import KeycloakConnection
from shared.crypto import decrypt_secret
from shared.schemas import (
    KeycloakConnectionResponseSerializer,
    KeycloakConnectionTestRequestSerializer,
    KeycloakConnectionTestResponseSerializer,
    KeycloakConnectionUpdateRequestSerializer,
)
from shared.throttling import AdminWriteThrottle, KeycloakConnectionTestRateThrottle


def _serialize_keycloak_connection(row: KeycloakConnection) -> dict:
    return {
        "enabled": row.enabled,
        "api_url": row.api_url,
        "admin_token_set": bool(row.admin_token_encrypted),
        "updated_at": row.updated_at,
        "updated_by_email": row.updated_by.email if row.updated_by else None,
    }


@extend_schema(tags=["Admin — Keycloak"])
class KeycloakConnectionAdminView(APIView):
    """
    Ver/editar a conexão central do PaperMoon com o Keycloak que ELE administra
    (provisionamento de realms/clients de clientes). NÃO é a config de SSO de
    staff (ver apps.accounts.views.SSOConfigAdminView) — Keycloaks diferentes.
    """

    permission_classes = [IsAdminUser]

    def get_throttles(self) -> list:
        if self.request.method == "PATCH":
            return [AdminWriteThrottle()]
        return super().get_throttles()

    @extend_schema(
        summary="Ver conexão central com o Keycloak",
        description="admin_token nunca é retornado em texto puro — só admin_token_set.",
        responses={200: KeycloakConnectionResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        row = KeycloakConnection.get_solo()
        return Response(_serialize_keycloak_connection(row))

    @extend_schema(
        summary="Atualizar conexão central com o Keycloak",
        description=(
            "admin_token em branco mantém o token já salvo. Ativar (enabled=true) "
            "exige api_url e um admin_token (novo ou já salvo)."
        ),
        request=KeycloakConnectionUpdateRequestSerializer,
        responses={200: KeycloakConnectionResponseSerializer},
    )
    def patch(self, request: Request) -> Response:
        serializer = KeycloakConnectionUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Campos ausentes do body (não apenas em branco) mantêm o valor já salvo —
        # desativar com só {"enabled": false} não pode apagar api_url.
        existing = KeycloakConnection.get_solo()
        api_url = data.get("api_url", existing.api_url)
        has_token = bool(data.get("admin_token") or existing.admin_token_encrypted)

        if data["enabled"] and not (api_url and has_token):
            return Response(
                {
                    "code": "validation_error",
                    "message": "api_url e admin_token são obrigatórios para ativar a conexão.",
                    "details": [],
                },
                status=400,
            )

        row = update_keycloak_connection(
            enabled=data["enabled"],
            api_url=api_url,
            admin_token=data.get("admin_token") or None,
            # permission_classes=[IsAdminUser] já garante autenticado — o cast só
            # ajuda o mypy, que não estreita request.user a partir de IsAdminUser.
            user=cast(CustomUser, request.user),
        )

        log_action(
            "keycloak_connection.updated",
            "KeycloakConnection",
            str(row.pk),
            user=request.user,
            request=request,
            changes={
                "enabled": row.enabled,
                "api_url": row.api_url,
                "admin_token_changed": bool(data.get("admin_token")),
            },
        )
        return Response(_serialize_keycloak_connection(row))


@extend_schema(tags=["Admin — Keycloak"])
class KeycloakConnectionTestView(APIView):
    """Testa conectividade autenticada com o Admin REST API do Keycloak central."""

    permission_classes = [IsAdminUser]
    throttle_classes = [KeycloakConnectionTestRateThrottle]

    @extend_schema(
        summary="Testar conectividade com o Keycloak central",
        description=(
            "Confirma que o Keycloak é alcançável e que o admin_token é aceito pelo "
            "Admin REST API. Se api_url/admin_token forem omitidos no body, usa os "
            "já salvos (decriptados no servidor, sem o admin precisar redigitar)."
        ),
        request=KeycloakConnectionTestRequestSerializer,
        responses={200: KeycloakConnectionTestResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        api_url = (request.data.get("api_url") or "").strip()
        admin_token = (request.data.get("admin_token") or "").strip()

        existing = KeycloakConnection.get_solo()
        if not api_url:
            api_url = existing.api_url
        if not admin_token:
            admin_token = decrypt_secret(existing.admin_token_encrypted)

        if not api_url:
            return Response(
                {
                    "code": "missing_fields",
                    "message": "Informe a api_url para testar.",
                    "details": [],
                },
                status=400,
            )
        if not admin_token:
            return Response(
                {
                    "code": "missing_fields",
                    "message": "Informe o admin_token para testar.",
                    "details": [],
                },
                status=400,
            )

        result = test_admin_connectivity(api_url, admin_token)
        return Response(result)
