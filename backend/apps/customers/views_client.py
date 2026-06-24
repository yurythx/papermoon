import csv
import io

from django.http import HttpResponse as DjangoHttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.queries import get_financial_metrics, list_invoices
from apps.billing.serializers import InvoiceSerializer
from apps.customers.commands import CreateInvitationCommand, RevokeInvitationCommand
from apps.customers.models import CustomerProfile, Invitation
from apps.customers.repositories import DjangoCustomerRepository
from apps.customers.serializers import (
    CreateInvitationSerializer,
    CustomerSerializer,
    InvitationSerializer,
)
from apps.customers.services import CustomerService
from shared.schemas import (
    ApiQuotaSerializer,
    FinancialMetricsSerializer,
    TeamMemberItemSerializer,
)


def _service() -> CustomerService:
    return CustomerService(DjangoCustomerRepository())


def _resolve_customer(user):
    profile = CustomerProfile.objects.filter(user=user).select_related("customer").first()
    if not profile:
        raise NotFound("Nenhum customer vinculado a este usuário.")
    return profile.customer


@extend_schema(tags=["Client — Perfil"])
class CustomerMeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Dados do meu customer", responses={200: CustomerSerializer})
    def get(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        return Response(CustomerSerializer(customer).data)

    @extend_schema(
        summary="Atualizar dados cadastrais",
        request=CustomerSerializer,
        responses={200: CustomerSerializer},
    )
    def patch(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        updated = _service().update_customer(customer.id, request.data)
        return Response(CustomerSerializer(updated).data)


@extend_schema(tags=["Client — Faturas"])
class ClientInvoiceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar minhas faturas",
        parameters=[
            OpenApiParameter("status", str, description="pending | paid | overdue | cancelled"),
            OpenApiParameter(
                "ordering", str, description="-due_date | due_date | -created_at | amount"
            ),
            OpenApiParameter("page", int),
        ],
        responses={200: InvoiceSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        filters = {}
        if status := request.query_params.get("status"):
            filters["status"] = status
        qs = list_invoices(customer.id, filters)

        # Ordering
        ordering = request.query_params.get("ordering", "-due_date")
        allowed = {"due_date", "-due_date", "created_at", "-created_at", "amount", "-amount"}
        if ordering in allowed:
            qs = qs.order_by(ordering)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(InvoiceSerializer(page, many=True).data)


@extend_schema(tags=["Client — Faturas"])
class ClientInvoiceExportView(APIView):
    """
    GET /api/v1/client/invoices/export/
    Returns all customer invoices as a CSV file download.
    Accepts optional ?status= filter (same values as the list endpoint).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Exportar faturas como CSV",
        parameters=[
            OpenApiParameter("status", str, description="pending | paid | overdue | cancelled"),
        ],
        responses={(200, "text/csv"): None},
    )
    def get(self, request: Request) -> DjangoHttpResponse:
        customer = _resolve_customer(request.user)
        filters = {}
        if status := request.query_params.get("status"):
            filters["status"] = status

        qs = list_invoices(customer.id, filters).order_by("-due_date")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["ID", "Status", "Valor (R$)", "Vencimento", "Criado em", "Asaas ID"])
        for inv in qs:
            writer.writerow(
                [
                    str(inv.id)[:8],
                    inv.status,
                    str(inv.amount),
                    inv.due_date.strftime("%Y-%m-%d"),
                    inv.created_at.strftime("%Y-%m-%d"),
                    inv.asaas_id or "",
                ]
            )

        response = DjangoHttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="faturas.csv"'
        return response


@extend_schema(tags=["Client — Métricas"])
class ClientFinancialMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Métricas financeiras do meu tenant",
        description="Retorna totais de faturas pagas, pendentes e vencidas.",
        responses={200: FinancialMetricsSerializer},
    )
    def get(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        raw = get_financial_metrics(customer.id)
        return Response(
            {
                "total_paid": float(raw["total_paid"]),
                "total_pending": float(raw["total_pending"]),
                "total_overdue": float(raw["total_overdue"]),
            }
        )


@extend_schema(tags=["Client — Licensing"])
class ClientApiQuotaView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Quota de chamadas de API do tenant",
        description="Retorna o uso atual e o limite de chamadas de API para o customer.",
        responses={200: ApiQuotaSerializer},
    )
    def get(self, request: Request) -> Response:
        from apps.licensing.models import LicenseQuota
        from apps.subscriptions.models import Subscription

        customer = _resolve_customer(request.user)

        sub = (
            Subscription.objects.select_related("product", "pricing")
            .filter(customer=customer, status=Subscription.Status.ACTIVE)
            .first()
        )
        plan_name = sub.product.name if sub else None
        plan_slug = sub.product.slug if sub else None
        billing_cycle = sub.pricing.billing_cycle if sub and sub.pricing else None

        try:
            quota = LicenseQuota.objects.get(customer=customer)
        except LicenseQuota.DoesNotExist:
            return Response(
                {
                    "used_api_calls": 0,
                    "max_api_calls": 0,
                    "reset_at": None,
                    "usage_pct": 0.0,
                    "plan_name": plan_name,
                    "plan_slug": plan_slug,
                    "billing_cycle": billing_cycle,
                }
            )
        usage_pct = (
            round(quota.used_api_calls / quota.max_api_calls * 100, 1)
            if quota.max_api_calls
            else 0.0
        )
        return Response(
            {
                "used_api_calls": quota.used_api_calls,
                "max_api_calls": quota.max_api_calls,
                "reset_at": quota.reset_at,
                "usage_pct": usage_pct,
                "plan_name": plan_name,
                "plan_slug": plan_slug,
                "billing_cycle": billing_cycle,
            }
        )


@extend_schema(tags=["Client — Equipe"])
class TeamMembersView(APIView):
    """List all users that belong to the same customer (tenant)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar membros da equipe", responses={200: TeamMemberItemSerializer(many=True)}
    )
    def get(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        profiles = (
            CustomerProfile.objects.filter(customer=customer)
            .select_related("user")
            .order_by("user__email")
        )
        data = [
            {
                "id": str(p.id),
                "email": p.user.email,
                "username": p.user.username,
                "role": p.role,
                "joined_at": p.user.date_joined.isoformat(),
                "is_you": p.user_id == request.user.pk,
            }
            for p in profiles
        ]
        return Response(data)


@extend_schema(tags=["Client — Convites"])
class InvitationListCreateView(APIView):
    """List pending invitations or send a new invite. Requires owner or admin role."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar convites enviados", responses={200: InvitationSerializer(many=True)}
    )
    def get(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        invitations = Invitation.objects.filter(customer=customer).order_by("-created_at")
        return Response(InvitationSerializer(invitations, many=True).data)

    @extend_schema(
        summary="Enviar convite por e-mail",
        description="Envia um convite para um novo usuário ingressar no tenant.",
        request=CreateInvitationSerializer,
        responses={201: InvitationSerializer},
    )
    def post(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        serializer = CreateInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = CreateInvitationCommand(
            customer_id=customer.id,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by_id=request.user.id,
        ).execute()
        return Response(InvitationSerializer(invitation).data, status=201)


@extend_schema(tags=["Client — Convites"])
class InvitationRevokeView(APIView):
    """Revoke a pending invitation. Requires owner or admin role."""

    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Revogar convite pendente", responses={204: None})
    def delete(self, request: Request, pk: str) -> Response:
        RevokeInvitationCommand(
            invitation_id=pk,
            revoked_by_id=request.user.id,
        ).execute()
        return Response(status=204)


@extend_schema(tags=["Client — Convites"])
class InvitationResendView(APIView):
    """Resend a pending or expired invitation (fresh token + new email). Requires owner or admin role."""

    permission_classes = [IsAuthenticated]
    serializer_class = InvitationSerializer

    @extend_schema(summary="Reenviar convite por e-mail", responses={200: InvitationSerializer})
    def post(self, request: Request, pk: str) -> Response:
        from apps.customers.commands import ResendInvitationCommand

        invitation = ResendInvitationCommand(
            invitation_id=pk,
            requested_by_id=request.user.id,
        ).execute()
        return Response(InvitationSerializer(invitation).data)


def _require_manager_role(requesting_profile: CustomerProfile) -> None:
    """Raises PermissionDenied if the caller is not owner or admin."""
    if requesting_profile.role not in (CustomerProfile.Role.OWNER, CustomerProfile.Role.ADMIN):
        raise PermissionDenied("Apenas proprietários e administradores podem gerenciar membros.")


@extend_schema(tags=["Client — Equipe"])
class TeamMemberDetailView(APIView):
    """Change a team member's role or remove them from the tenant."""

    permission_classes = [IsAuthenticated]

    def _get_profiles(self, request: Request, pk: str):
        customer = _resolve_customer(request.user)
        requesting_profile = CustomerProfile.objects.filter(
            user=request.user, customer=customer
        ).first()
        if not requesting_profile:
            raise NotFound("Perfil não encontrado.")
        target_profile = (
            CustomerProfile.objects.filter(pk=pk, customer=customer).select_related("user").first()
        )
        if not target_profile:
            raise NotFound("Membro não encontrado.")
        return requesting_profile, target_profile

    @extend_schema(
        summary="Alterar papel de um membro",
        request={
            "application/json": {
                "type": "object",
                "properties": {"role": {"type": "string", "enum": ["admin", "member"]}},
            }
        },
        responses={200: TeamMemberItemSerializer},
    )
    def patch(self, request: Request, pk: str) -> Response:
        requesting_profile, target_profile = self._get_profiles(request, pk)
        _require_manager_role(requesting_profile)

        if target_profile.role == CustomerProfile.Role.OWNER:
            raise PermissionDenied("O papel do proprietário não pode ser alterado.")
        if target_profile.user_id == request.user.pk:
            raise PermissionDenied("Você não pode alterar seu próprio papel.")

        new_role = request.data.get("role")
        if new_role not in ("admin", "member"):
            raise ValidationError({"role": "Papel inválido. Use 'admin' ou 'member'."})

        target_profile.role = new_role
        target_profile.save(update_fields=["role"])

        return Response(
            {
                "id": str(target_profile.pk),
                "email": target_profile.user.email,
                "username": target_profile.user.username,
                "role": target_profile.role,
                "joined_at": target_profile.user.date_joined.isoformat(),
                "is_you": False,
            }
        )

    @extend_schema(summary="Remover membro da equipe", responses={204: None})
    def delete(self, request: Request, pk: str) -> Response:
        requesting_profile, target_profile = self._get_profiles(request, pk)
        _require_manager_role(requesting_profile)

        if target_profile.role == CustomerProfile.Role.OWNER:
            raise PermissionDenied("O proprietário não pode ser removido.")
        if target_profile.user_id == request.user.pk:
            raise PermissionDenied("Você não pode remover a si mesmo.")

        target_profile.delete()
        return Response(status=204)
