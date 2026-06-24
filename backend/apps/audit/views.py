from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer


@extend_schema(tags=["Admin — Audit"])
class AuditLogListView(APIView):
    """Read-only audit trail. Admin only."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Audit log — trilha de auditoria",
        parameters=[
            OpenApiParameter("resource_type", str, description="Ex: Customer, Subscription"),
            OpenApiParameter("resource_id", str, description="UUID do recurso"),
            OpenApiParameter("action", str, description="Ex: customer.created, suspend_customer"),
        ],
        responses={200: AuditLogSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = AuditLog.objects.select_related("user").all()

        if resource_type := request.query_params.get("resource_type"):
            qs = qs.filter(resource_type=resource_type)
        if resource_id := request.query_params.get("resource_id"):
            qs = qs.filter(resource_id=resource_id)
        if action := request.query_params.get("action"):
            qs = qs.filter(action=action)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AuditLogSerializer(page, many=True).data)
