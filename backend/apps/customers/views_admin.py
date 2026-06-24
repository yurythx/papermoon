from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.utils import log_action
from apps.billing.queries import get_mrr_metrics
from apps.customers.models import Customer
from apps.customers.repositories import DjangoCustomerRepository
from apps.customers.serializers import CustomerSerializer
from apps.customers.services import CustomerService
from shared.schemas import (
    MessageResponseSerializer,
    MRRMetricsSerializer,
    SuspendReasonRequestSerializer,
)
from shared.throttling import AdminWriteThrottle


class _QuotaSerializer(serializers.Serializer):
    max_api_calls = serializers.IntegerField()
    used_api_calls = serializers.IntegerField()
    reset_at = serializers.DateTimeField(allow_null=True)


def _service() -> CustomerService:
    return CustomerService(DjangoCustomerRepository())


def _transition(request: Request, pk: str, method: str) -> Response:
    service = _service()
    try:
        customer = getattr(service, method)(pk)
    except ValueError as exc:
        return Response(
            {"code": "invalid_transition", "message": str(exc), "details": []},
            status=400,
        )
    log_action(method, "Customer", customer.id, user=request.user, request=request)
    return Response(CustomerSerializer(customer).data)


@extend_schema(tags=["Admin — Customers"])
class CustomerListCreateView(APIView):
    permission_classes = [IsAdminUser]
    # queryset=none() lets drf-spectacular resolve the model without calling get_queryset().
    queryset = Customer.objects.none()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status"]
    ordering_fields = ["company_name", "created_at", "updated_at"]
    ordering = ["-created_at"]
    search_fields = ["company_name", "document"]

    def get_throttles(self):
        if self.request.method == "POST":
            return [AdminWriteThrottle()]
        return super().get_throttles()

    @extend_schema(
        operation_id="admin_customers_list",
        summary="Listar todos os customers",
        parameters=[
            OpenApiParameter("status", str, description="active | suspended | cancelled"),
            OpenApiParameter("search", str, description="Busca por razão social ou CNPJ"),
            OpenApiParameter(
                "ordering", str, description="-created_at | company_name | updated_at"
            ),
            OpenApiParameter("page", int),
        ],
        responses={200: CustomerSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = DjangoCustomerRepository().get_all()
        # Apply filter/search/ordering backends manually (APIView doesn't do it automatically)
        for backend in [DjangoFilterBackend(), OrderingFilter(), SearchFilter()]:
            qs = backend.filter_queryset(request, qs, self)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(CustomerSerializer(page, many=True).data)

    @extend_schema(
        summary="Criar novo customer (tenant)",
        request=CustomerSerializer,
        responses={201: CustomerSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = CustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = _service().create_customer(serializer.validated_data)
        log_action("customer.created", "Customer", customer.id, user=request.user, request=request)
        return Response(CustomerSerializer(customer).data, status=201)


@extend_schema(tags=["Admin — Customers"])
class CustomerDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(summary="Detalhe de um customer", responses={200: CustomerSerializer})
    def get(self, request: Request, pk: str) -> Response:
        customer = _service().get_customer(pk)
        return Response(CustomerSerializer(customer).data)


@extend_schema(tags=["Admin — Customers"])
class CustomerSuspendView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Suspender customer",
        description="Muda status para 'suspended' e desativa todas as API Keys e acessos.",
        request=SuspendReasonRequestSerializer,
        responses={200: CustomerSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        return _transition(request, pk, "suspend_customer")


@extend_schema(tags=["Admin — Customers"])
class CustomerReactivateView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Reativar customer suspenso", request=None, responses={200: CustomerSerializer}
    )
    def post(self, request: Request, pk: str) -> Response:
        return _transition(request, pk, "reactivate_customer")


@extend_schema(tags=["Admin — Customers"])
class CustomerCancelView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Cancelar customer",
        description="Transição irreversível para 'cancelled'. Use com cuidado.",
        request=None,
        responses={200: CustomerSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        return _transition(request, pk, "cancel_customer")


@extend_schema(tags=["Admin — Customers"])
class CustomerSoftDeleteView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(
        summary="Soft-delete customer",
        description=(
            "Marca o customer como deletado (deleted_at). "
            "O registro permanece no banco mas fica invisível via API normal."
        ),
        responses={200: MessageResponseSerializer},
    )
    def delete(self, request: Request, pk: str) -> Response:
        from rest_framework.exceptions import NotFound as DRFNotFound

        try:
            customer = _service().soft_delete_customer(pk)
        except DRFNotFound:
            return Response(
                {"code": "not_found", "message": "Customer não encontrado.", "details": []},
                status=404,
            )
        except ValueError as exc:
            return Response(
                {"code": "already_deleted", "message": str(exc), "details": []},
                status=400,
            )
        log_action("customer.deleted", "Customer", customer.id, user=request.user, request=request)
        return Response({"message": "Customer removido com sucesso."}, status=200)


@extend_schema(tags=["Admin — Metrics"])
class AdminMetricsView(APIView):
    """Platform-wide MRR/ARR dashboard. Admin only."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Dashboard de métricas (MRR/ARR/churn)", responses={200: MRRMetricsSerializer}
    )
    def get(self, request: Request) -> Response:
        data = get_mrr_metrics()
        data["mrr"] = float(data["mrr"])
        data["arr"] = float(data["arr"])
        for row in data["monthly_revenue"]:
            row["revenue"] = float(row["revenue"])
        for row in data.get("revenue_by_plan", []):
            row["revenue"] = float(row["revenue"])
        return Response(data)


@extend_schema(tags=["Admin — Customers"])
class CustomerQuotaView(APIView):
    """Consultar e ajustar o limite de chamadas de API de um customer."""

    permission_classes = [IsAdminUser]
    throttle_classes = [AdminWriteThrottle]

    @extend_schema(summary="Consultar quota de API do customer", responses={200: _QuotaSerializer})
    def get(self, request: Request, pk: str) -> Response:
        from apps.licensing.models import LicenseQuota

        try:
            quota = LicenseQuota.objects.get(customer_id=pk)
        except LicenseQuota.DoesNotExist:
            return Response({"max_api_calls": None, "used_api_calls": 0, "reset_at": None})
        return Response(
            {
                "max_api_calls": quota.max_api_calls,
                "used_api_calls": quota.used_api_calls,
                "reset_at": quota.reset_at,
            }
        )

    @extend_schema(
        summary="Atualizar limite de chamadas de API do customer",
        request=_QuotaSerializer,
        responses={200: _QuotaSerializer},
    )
    def patch(self, request: Request, pk: str) -> Response:
        from apps.licensing.models import LicenseQuota

        try:
            customer = Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return Response(
                {"code": "not_found", "message": "Customer não encontrado.", "details": []},
                status=404,
            )
        try:
            quota = LicenseQuota.objects.get(customer=customer)
        except LicenseQuota.DoesNotExist:
            return Response(
                {
                    "code": "not_found",
                    "message": "Quota não configurada para este customer.",
                    "details": [],
                },
                status=404,
            )

        raw = request.data.get("max_api_calls")
        if raw is None:
            return Response(
                {
                    "code": "validation_error",
                    "message": "max_api_calls é obrigatório.",
                    "details": [],
                },
                status=400,
            )
        try:
            quota.max_api_calls = int(raw)
        except (ValueError, TypeError):
            return Response(
                {
                    "code": "validation_error",
                    "message": "max_api_calls deve ser um inteiro.",
                    "details": [],
                },
                status=400,
            )
        quota.save(update_fields=["max_api_calls"])
        log_action("quota.updated", "Customer", customer.id, user=request.user, request=request)
        return Response(
            {
                "max_api_calls": quota.max_api_calls,
                "used_api_calls": quota.used_api_calls,
                "reset_at": quota.reset_at,
            }
        )
