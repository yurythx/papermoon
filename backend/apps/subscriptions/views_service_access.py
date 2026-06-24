"""
Admin and client views for ServiceAccess management.

Each subscription has one License; each License has N ServiceAccess
records (one per microservice included in the product).
These endpoints let admins manage services independently of the subscription lifecycle.
"""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.subscriptions.models import ServiceAccess
from apps.subscriptions.serializers import ServiceAccessSerializer
from shared.schemas import ServiceAccessCreateRequestSerializer, ServiceAccessPatchRequestSerializer

logger = logging.getLogger(__name__)


def _get_subscription(pk: str):
    from django.shortcuts import get_object_or_404

    from apps.subscriptions.models import Subscription

    return get_object_or_404(Subscription.objects.select_related("license"), pk=pk)


# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------


@extend_schema(tags=["Admin — Service Accesses"])
class AdminServiceAccessListCreateView(APIView):
    """
    GET  /api/v1/admin/subscriptions/<sub_id>/services/  — list all service accesses
    POST /api/v1/admin/subscriptions/<sub_id>/services/  — add a new service to the license
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Listar acessos de serviço da assinatura",
        responses={200: ServiceAccessSerializer(many=True)},
    )
    def get(self, request: Request, subscription_pk: str) -> Response:
        sub = _get_subscription(subscription_pk)
        qs = ServiceAccess.objects.filter(license=sub.license).order_by("service_key")
        return Response(ServiceAccessSerializer(qs, many=True).data)

    @extend_schema(
        summary="Adicionar serviço à assinatura",
        request=ServiceAccessCreateRequestSerializer,
        responses={201: ServiceAccessSerializer},
    )
    def post(self, request: Request, subscription_pk: str) -> Response:
        from apps.products.models import ServiceComponent

        sub = _get_subscription(subscription_pk)
        service_key = request.data.get("service_key", "").strip()

        if not service_key:
            raise ValidationError({"service_key": "This field is required."})

        valid_keys = [k for k, _ in ServiceComponent.SERVICE_KEY_CHOICES]
        if service_key not in valid_keys:
            raise ValidationError({"service_key": f"Invalid service. Choices: {valid_keys}"})

        if ServiceAccess.objects.filter(license=sub.license, service_key=service_key).exists():
            raise ValidationError(
                {"service_key": f"Service '{service_key}' already exists on this license."}
            )

        sa = ServiceAccess.objects.create(
            license=sub.license,
            service_key=service_key,
            status=ServiceAccess.Status.PROVISIONING,
            config=request.data.get("config", {}),
        )

        # Fire provisioning immediately via OutboxEvent
        from shared.models import OutboxEvent

        OutboxEvent.objects.create(
            event_type="service_access.provision",
            payload={
                "service_access_id": str(sa.id),
                "license_id": str(sub.license.id),
                "customer_id": str(sub.customer_id),
                "service_key": service_key,
                "config": sa.config,
            },
        )

        return Response(ServiceAccessSerializer(sa).data, status=201)


@extend_schema(tags=["Admin — Service Accesses"])
class AdminServiceAccessDetailView(APIView):
    """
    GET    /api/v1/admin/service-accesses/<id>/           — detail
    PATCH  /api/v1/admin/service-accesses/<id>/           — update config
    DELETE /api/v1/admin/service-accesses/<id>/           — deprovision and remove
    """

    permission_classes = [IsAdminUser]

    def _get(self, pk: str) -> ServiceAccess:
        from django.shortcuts import get_object_or_404

        return get_object_or_404(ServiceAccess, pk=pk)

    @extend_schema(summary="Detalhe de acesso de serviço", responses={200: ServiceAccessSerializer})
    def get(self, request: Request, pk: str) -> Response:
        return Response(ServiceAccessSerializer(self._get(pk)).data)

    @extend_schema(
        summary="Atualizar config/external_id do serviço",
        request=ServiceAccessPatchRequestSerializer,
        responses={200: ServiceAccessSerializer},
    )
    def patch(self, request: Request, pk: str) -> Response:
        sa = self._get(pk)
        allowed_fields = {"config", "external_id"}
        for field in allowed_fields:
            if field in request.data:
                setattr(sa, field, request.data[field])
        sa.save(update_fields=[*list(allowed_fields & request.data.keys()), "updated_at"])
        return Response(ServiceAccessSerializer(sa).data)

    @extend_schema(summary="Desprovisionar serviço", responses={204: None})
    def delete(self, request: Request, pk: str) -> Response:
        sa = self._get(pk)
        from shared.models import OutboxEvent

        OutboxEvent.objects.create(
            event_type="service_access.deprovision",
            payload={
                "service_access_id": str(sa.id),
                "license_id": str(sa.license_id),
                "customer_id": str(sa.license.customer_id),
                "service_key": sa.service_key,
                "external_id": sa.external_id,
            },
        )
        sa.status = ServiceAccess.Status.DEPROVISIONED
        sa.save(update_fields=["status", "updated_at"])
        return Response(status=204)


@extend_schema(tags=["Admin — Service Accesses"])
class AdminServiceAccessReprovisionView(APIView):
    """
    POST /api/v1/admin/service-accesses/<id>/reprovision/
    Re-triggers provisioning for a FAILED or PROVISIONING service access.
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Re-provisionar serviço com falha",
        request=None,
        responses={200: ServiceAccessSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        from django.shortcuts import get_object_or_404

        from shared.models import OutboxEvent

        sa = get_object_or_404(ServiceAccess.objects.select_related("license"), pk=pk)

        if sa.status not in {ServiceAccess.Status.FAILED, ServiceAccess.Status.PROVISIONING}:
            raise ValidationError(
                {"status": f"Cannot reprovision a service in '{sa.status}' state."}
            )

        sa.status = ServiceAccess.Status.PROVISIONING
        sa.error = None
        sa.save(update_fields=["status", "error", "updated_at"])

        OutboxEvent.objects.create(
            event_type="service_access.provision",
            payload={
                "service_access_id": str(sa.id),
                "license_id": str(sa.license_id),
                "customer_id": str(sa.license.customer_id),
                "service_key": sa.service_key,
                "config": sa.config,
            },
        )

        return Response(ServiceAccessSerializer(sa).data)


# ---------------------------------------------------------------------------
# Client view — read-only, filtered to own customer
# ---------------------------------------------------------------------------


@extend_schema(tags=["Client — Assinaturas"])
class ClientServiceAccessListView(APIView):
    """
    GET /api/v1/client/subscriptions/<sub_id>/services/
    Returns service accesses for the logged-in customer's subscription.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar serviços ativos da minha assinatura",
        responses={200: ServiceAccessSerializer(many=True)},
    )
    def get(self, request: Request, subscription_pk: str) -> Response:
        from django.shortcuts import get_object_or_404

        from apps.customers.models import CustomerProfile
        from apps.subscriptions.models import Subscription

        profile = (
            CustomerProfile.objects.filter(user=request.user).select_related("customer").first()
        )
        if not profile:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied()

        sub = get_object_or_404(Subscription, pk=subscription_pk, customer=profile.customer)
        qs = ServiceAccess.objects.filter(license=sub.license).order_by("service_key")
        return Response(ServiceAccessSerializer(qs, many=True).data)
