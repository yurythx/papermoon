from django.conf import settings
from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from shared.email import send_html_email


class _HealthSerializer(serializers.Serializer):
    db = serializers.CharField()
    redis = serializers.CharField()
    celery = serializers.CharField()


@extend_schema(tags=["Health"])
class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []  # Health checks must never be rate-limited (called by LB / monitoring)

    @extend_schema(
        summary="Health check — DB, Redis e Celery",
        responses={200: _HealthSerializer, 503: _HealthSerializer},
    )
    def get(self, request: Request) -> Response:
        checks: dict[str, str] = {}

        try:
            connection.ensure_connection()
            checks["db"] = "ok"
        except Exception:
            checks["db"] = "error"

        try:
            cache.set("health_check", "1", timeout=5)
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "error"

        try:
            from celery import current_app

            result = current_app.control.inspect(timeout=1).ping()
            checks["celery"] = "ok" if result else "degraded"
        except Exception:
            checks["celery"] = "error"

        # 503 only when a critical service (db or redis) is in error state.
        # Celery "degraded" means no workers running — app still serves requests.
        critical = {k: checks[k] for k in ("db", "redis") if k in checks}
        status_code = 200 if all(v == "ok" for v in critical.values()) else 503
        return Response(checks, status=status_code)


class _ContactThrottle(AnonRateThrottle):
    rate = "5/hour"
    scope = "contact"


class _ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    service = serializers.CharField(max_length=80, required=False, allow_blank=True)
    message = serializers.CharField(max_length=2000)


@extend_schema(tags=["Contact"])
class ContactView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [_ContactThrottle]

    @extend_schema(
        summary="Formulário de contato público",
        request=_ContactSerializer,
        responses={200: None},
    )
    def post(self, request: Request) -> Response:
        serializer = _ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        send_html_email(
            subject=f"[Contato PaperMoon] {data['name']} — {data.get('service') or 'Geral'}",
            recipient=settings.DEFAULT_FROM_EMAIL,
            template_name="contact_internal",
            context={
                "name": data["name"],
                "email": data["email"],
                "phone": data.get("phone") or "—",
                "service": data.get("service") or "Não informado",
                "message": data["message"],
            },
        )

        return Response({"detail": "Mensagem enviada com sucesso."}, status=status.HTTP_200_OK)
