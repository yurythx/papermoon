from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.flags.models import FeatureFlag
from apps.flags.serializers import FeatureFlagSerializer
from shared.throttling import AdminWriteThrottle


@extend_schema(tags=["Admin — Feature Flags"])
class FeatureFlagListCreateView(APIView):
    """GET  /api/v1/admin/feature-flags/  — lista todas as flags.
    POST /api/v1/admin/feature-flags/  — cria uma flag nova (desligada por padrão)."""

    permission_classes = [IsAdminUser]

    def get_throttles(self) -> list:
        if self.request.method == "POST":
            return [AdminWriteThrottle()]
        return super().get_throttles()

    @extend_schema(
        summary="Listar feature flags", responses={200: FeatureFlagSerializer(many=True)}
    )
    def get(self, request: Request) -> Response:
        flags = FeatureFlag.objects.prefetch_related("enabled_customers").all()
        return Response(FeatureFlagSerializer(flags, many=True).data)

    @extend_schema(
        summary="Criar feature flag",
        request=FeatureFlagSerializer,
        responses={201: FeatureFlagSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = FeatureFlagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        flag = serializer.save()
        return Response(FeatureFlagSerializer(flag).data, status=201)


@extend_schema(tags=["Admin — Feature Flags"])
class FeatureFlagDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/admin/feature-flags/<id>/"""

    permission_classes = [IsAdminUser]

    def get_throttles(self) -> list:
        if self.request.method in ("PATCH", "DELETE"):
            return [AdminWriteThrottle()]
        return super().get_throttles()

    def _get_flag(self, pk: int) -> FeatureFlag:
        try:
            return FeatureFlag.objects.prefetch_related("enabled_customers").get(pk=pk)
        except (FeatureFlag.DoesNotExist, ValueError):
            raise NotFound("Flag não encontrada.") from None

    @extend_schema(summary="Detalhe de uma feature flag", responses={200: FeatureFlagSerializer})
    def get(self, request: Request, pk: int) -> Response:
        return Response(FeatureFlagSerializer(self._get_flag(pk)).data)

    @extend_schema(
        summary="Atualizar feature flag (inclui ligar/desligar globalmente ou por customer)",
        request=FeatureFlagSerializer,
        responses={200: FeatureFlagSerializer},
    )
    def patch(self, request: Request, pk: int) -> Response:
        flag = self._get_flag(pk)
        serializer = FeatureFlagSerializer(flag, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(FeatureFlagSerializer(self._get_flag(pk)).data)

    @extend_schema(summary="Remover feature flag", responses={204: None})
    def delete(self, request: Request, pk: int) -> Response:
        self._get_flag(pk).delete()
        return Response(status=204)
