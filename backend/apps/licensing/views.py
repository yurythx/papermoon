import logging

from django.core.cache import cache
from django.db.models import F
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.licensing.commands import CreateApiKeyCommand, RevokeApiKeyCommand
from apps.licensing.models import ApiKey
from apps.licensing.queries import list_api_keys
from shared.schemas import (
    ApiKeyCreateResponseSerializer,
    ApiKeyItemSerializer,
    ValidateApiKeyResponseSerializer,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 60  # seconds


@extend_schema(tags=["Licensing"])
class ValidateKeyView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Validar API Key (endpoint público)",
        description=(
            "Verifica se uma API Key é válida, tem licença ativa e quota disponível. "
            "Resultado cacheado por 60s no Redis. Chamado pelo n8n a cada requisição."
        ),
        parameters=[
            OpenApiParameter("key", str, required=True, description="API Key a ser validada")
        ],
        responses={200: ValidateApiKeyResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        key = request.query_params.get("key", "")
        if not key:
            return Response(
                {"code": "missing_key", "message": "Parâmetro 'key' é obrigatório.", "details": []},
                status=400,
            )

        cache_key = f"apikey:{key}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        try:
            api_key = ApiKey.objects.select_related("customer__quota").get(key=key, is_active=True)
        except ApiKey.DoesNotExist:
            result = {"valid": False, "reason": "invalid_key", "quota_remaining": 0}
            cache.set(cache_key, result, timeout=_CACHE_TTL)
            return Response(result)

        # Check that the customer has at least one active license (subscription-based access)
        from apps.subscriptions.models import License

        has_active_license = License.objects.filter(
            customer=api_key.customer,
            status=License.Status.ACTIVE,
        ).exists()
        if not has_active_license:
            result = {"valid": False, "reason": "no_active_license", "quota_remaining": 0}
            cache.set(cache_key, result, timeout=_CACHE_TTL)
            return Response(result)

        quota = getattr(api_key.customer, "quota", None)
        if quota is None:
            result = {"valid": True, "quota_remaining": None}
            cache.set(cache_key, result, timeout=_CACHE_TTL)
            return Response(result)

        remaining = quota.max_api_calls - quota.used_api_calls
        if remaining <= 0:
            result = {"valid": False, "reason": "quota_exceeded", "quota_remaining": 0}
            cache.set(cache_key, result, timeout=_CACHE_TTL)
            return Response(result)

        # Increment atomically — never read-then-write
        from apps.licensing.models import LicenseQuota

        LicenseQuota.objects.filter(customer=api_key.customer).update(
            used_api_calls=F("used_api_calls") + 1
        )

        result = {"valid": True, "quota_remaining": remaining - 1}
        cache.set(cache_key, result, timeout=_CACHE_TTL)
        return Response(result)


@extend_schema(tags=["Client — API Keys"])
class ApiKeyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar minhas API Keys", responses={200: ApiKeyItemSerializer(many=True)}
    )
    def get(self, request: Request) -> Response:
        from apps.customers.models import CustomerProfile

        profile = CustomerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response([], status=200)
        return Response(list(list_api_keys(profile.customer_id)))

    @extend_schema(
        summary="Gerar nova API Key",
        description="Cria uma nova API Key ativa para o tenant do usuário logado.",
        request=None,
        responses={201: ApiKeyCreateResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        from apps.customers.models import CustomerProfile

        profile = CustomerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response(
                {"code": "no_customer", "message": "Nenhum customer vinculado.", "details": []},
                status=400,
            )
        api_key = CreateApiKeyCommand().execute(profile.customer)
        return Response(
            {"id": str(api_key.id), "key": api_key.key, "is_active": api_key.is_active},
            status=201,
        )


@extend_schema(tags=["Client — API Keys"])
class ApiKeyRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Revogar API Key",
        description="Desativa a chave e invalida o cache Redis imediatamente.",
        responses={204: None},
    )
    def delete(self, request: Request, pk: str) -> Response:
        from rest_framework.exceptions import NotFound

        from apps.customers.models import CustomerProfile

        profile = CustomerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response(status=404)

        try:
            RevokeApiKeyCommand().execute(pk, profile.customer_id)
        except NotFound:
            return Response(status=404)

        return Response(status=204)


@extend_schema(tags=["Client — API Keys"])
class DailyApiUsageView(APIView):
    """
    GET /api/v1/client/api-keys/usage/daily/?days=30
    Returns daily API call counts for the last N days (max 90).
    Missing days are filled with 0 so the client always gets a complete series.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Histórico diário de uso de API",
        parameters=[
            OpenApiParameter(
                "days",
                int,
                description="Número de dias (padrão 30, máximo 90)",
                required=False,
            )
        ],
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "format": "date"},
                        "calls": {"type": "integer"},
                    },
                },
            }
        },
    )
    def get(self, request: Request) -> Response:
        from datetime import date, timedelta

        from apps.customers.models import CustomerProfile
        from apps.licensing.models import DailyApiUsage

        profile = CustomerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response([])

        try:
            days = max(1, min(int(request.query_params.get("days", 30)), 90))
        except (TypeError, ValueError):
            days = 30

        today = date.today()
        start = today - timedelta(days=days - 1)

        rows = {
            row["date"]: row["calls_count"]
            for row in DailyApiUsage.objects.filter(
                customer=profile.customer,
                date__gte=start,
                date__lte=today,
            ).values("date", "calls_count")
        }

        series = [
            {
                "date": (start + timedelta(days=i)).isoformat(),
                "calls": rows.get(start + timedelta(days=i), 0),
            }
            for i in range(days)
        ]
        return Response(series)
