from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.utils import log_action
from apps.subscriptions.commands import (
    CancelSubscriptionCommand,
    ChangeSubscriptionPlanCommand,
    CreateSubscriptionCommand,
    RenewSubscriptionCommand,
    SuspendSubscriptionCommand,
)
from apps.subscriptions.models import Subscription
from apps.subscriptions.serializers import CreateSubscriptionSerializer, SubscriptionSerializer
from shared.schemas import (
    ChangePlanRequestSerializer,
    SuspendReasonRequestSerializer,
)
from shared.throttling import AdminWriteThrottle


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
        from rest_framework.exceptions import ValidationError

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
