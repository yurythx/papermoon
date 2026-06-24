import datetime
import logging

from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.tasks import handle_asaas_payment_overdue, handle_asaas_payment_received
from shared.public_urls import sanitize_payment_url
from shared.schemas import (
    AdminInvoiceRowSerializer,
    APIUsageRowSerializer,
    MessageResponseSerializer,
    MRRMetricsSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["Webhooks"], request=None, responses={200: None})
class AsaasWebhookView(APIView):
    """
    Public endpoint that receives Asaas payment events.

    Security: validates the asaas-access-token header before any processing.
    Idempotency: ConfirmPaymentCommand and MarkOverdueCommand are safe to replay.
    No gateway HTTP calls are made here — Asaas is the caller, not the callee.
    """

    permission_classes = [AllowAny]
    throttle_classes = []  # Asaas may send bursts; security is the asaas-access-token header

    @extend_schema(
        summary="Webhook de eventos Asaas",
        description=(
            "Recebe eventos PAYMENT_RECEIVED e PAYMENT_OVERDUE do Asaas. "
            "Requer header `asaas-access-token` com o token configurado em ASAAS_WEBHOOK_TOKEN."
        ),
        request=None,
    )
    def post(self, request: Request) -> Response:
        if request.headers.get("asaas-access-token", "") != settings.ASAAS_WEBHOOK_TOKEN:
            return Response(
                {"code": "forbidden", "message": "Token inválido.", "details": []},
                status=403,
            )

        event = request.data.get("event", "")
        payment = request.data.get("payment", {})
        asaas_id = payment.get("id", "")
        webhook_id = request.data.get("id", "")

        # Idempotency: ignore duplicate deliveries from Asaas.
        if webhook_id:
            from apps.billing.models import WebhookEvent

            _, created = WebhookEvent.objects.get_or_create(
                asaas_event_id=webhook_id,
                defaults={"event_type": event},
            )
            if not created:
                logger.info("AsaasWebhook duplicate delivery skipped webhook_id=%s", webhook_id)
                return Response({"received": True})

        try:
            from apps.billing.models import Invoice

            invoice = Invoice.objects.get(asaas_id=asaas_id)
        except Invoice.DoesNotExist:
            logger.warning("AsaasWebhook invoice not found asaas_id=%s", asaas_id)
            return Response({"received": True})

        if event == "PAYMENT_RECEIVED":
            handle_asaas_payment_received.delay(str(invoice.id))
        elif event in ("PAYMENT_OVERDUE", "PAYMENT_DELETED"):
            handle_asaas_payment_overdue.delay(str(invoice.id))
        else:
            logger.info("AsaasWebhook unhandled event=%s", event)

        # Return immediately — processing happens asynchronously in Celery.
        return Response({"received": True})


@extend_schema(tags=["Admin — Billing"])
class AdminInvoiceListView(APIView):
    """GET /api/v1/billing/invoices/ — list all invoices across all customers. Admin only."""

    permission_classes = [IsAdminUser]
    serializer_class = AdminInvoiceRowSerializer

    @extend_schema(
        summary="Listar todas as faturas (admin)",
        parameters=[
            OpenApiParameter("status", str),
            OpenApiParameter("invoice_type", str),
            OpenApiParameter("customer_id", str),
            OpenApiParameter("page", int),
        ],
        responses={200: AdminInvoiceRowSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        from django.core.paginator import Paginator

        from apps.billing.queries import list_all_invoices

        try:
            page_num = int(request.query_params.get("page", 1))
        except ValueError:
            page_num = 1

        qs = list_all_invoices(
            status=request.query_params.get("status") or None,
            invoice_type=request.query_params.get("invoice_type") or None,
            customer_id=request.query_params.get("customer_id") or None,
        )

        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(page_num)

        results = [
            {
                "id": str(inv.id),
                "customer_id": str(inv.customer_id),
                "company_name": inv.customer.company_name,
                "invoice_type": inv.invoice_type,
                "billing_type": inv.billing_type,
                "description": inv.description,
                "amount": str(inv.amount),
                "status": inv.status,
                "due_date": inv.due_date.isoformat(),
                "asaas_id": inv.asaas_id,
                "payment_url": sanitize_payment_url(inv.payment_url),
                "created_at": inv.created_at.isoformat(),
            }
            for inv in page_obj
        ]
        return Response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "page": page_obj.number,
                "results": results,
            }
        )

    @extend_schema(
        summary="Criar fatura avulsa (admin)",
        description="Cria uma fatura de implantação ou suporte sem subscription vinculada.",
        responses={201: AdminInvoiceRowSerializer},
    )
    def post(self, request: Request) -> Response:
        from rest_framework.exceptions import NotFound as DRFNotFound

        from apps.billing.commands import CreateManualInvoiceCommand
        from apps.billing.models import Invoice
        from apps.billing.repositories import DjangoInvoiceRepository
        from apps.customers.repositories import DjangoCustomerRepository

        customer_id = request.data.get("customer_id")
        amount = request.data.get("amount")
        due_date_raw = request.data.get("due_date")
        invoice_type = request.data.get("invoice_type", Invoice.Type.SUPPORT)
        description = request.data.get("description", "")

        if not customer_id or not amount or not due_date_raw:
            return Response(
                {
                    "code": "validation_error",
                    "message": "customer_id, amount e due_date são obrigatórios.",
                    "details": [],
                },
                status=400,
            )

        try:
            due_date = datetime.date.fromisoformat(due_date_raw)
        except (TypeError, ValueError):
            return Response(
                {
                    "code": "validation_error",
                    "message": "due_date deve estar no formato YYYY-MM-DD.",
                    "details": [],
                },
                status=400,
            )

        if invoice_type not in {c[0] for c in Invoice.Type.choices}:
            return Response(
                {
                    "code": "validation_error",
                    "message": f"invoice_type inválido: {invoice_type}",
                    "details": [],
                },
                status=400,
            )

        billing_type = request.data.get("billing_type", "BOLETO").upper()
        if billing_type not in {c[0] for c in Invoice.BillingType.choices}:
            billing_type = Invoice.BillingType.BOLETO

        command = CreateManualInvoiceCommand(
            invoice_repository=DjangoInvoiceRepository(),
            customer_repository=DjangoCustomerRepository(),
        )
        try:
            inv = command.execute(
                customer_id=customer_id,
                invoice_type=invoice_type,
                billing_type=billing_type,
                amount=amount,
                due_date=due_date,
                description=description,
            )
        except DRFNotFound:
            return Response(
                {"code": "not_found", "message": "Customer não encontrado.", "details": []},
                status=404,
            )
        except Exception as exc:
            logger.error("AdminInvoiceListView.post error=%s", exc)
            return Response(
                {"code": "server_error", "message": str(exc), "details": []}, status=500
            )

        return Response(
            {
                "id": str(inv.id),
                "customer_id": str(inv.customer_id),
                "company_name": inv.customer.company_name,
                "invoice_type": inv.invoice_type,
                "billing_type": inv.billing_type,
                "description": inv.description,
                "amount": str(inv.amount),
                "status": inv.status,
                "due_date": inv.due_date.isoformat(),
                "asaas_id": inv.asaas_id,
                "payment_url": sanitize_payment_url(inv.payment_url),
                "created_at": inv.created_at.isoformat(),
            },
            status=201,
        )


@extend_schema(tags=["Admin — Billing"])
class AdminInvoiceSoftDeleteView(APIView):
    """DELETE /api/v1/billing/invoices/<pk>/ — soft-delete a single invoice."""

    permission_classes = [IsAdminUser]

    @extend_schema(summary="Soft-delete de fatura", responses={200: MessageResponseSerializer})
    def delete(self, request: Request, pk: str) -> Response:
        from apps.billing.models import Invoice

        try:
            invoice = Invoice.all_objects.get(pk=pk)
        except Invoice.DoesNotExist:
            return Response(
                {"code": "not_found", "message": "Fatura não encontrada.", "details": []},
                status=404,
            )
        if invoice.is_deleted:
            return Response(
                {"code": "already_deleted", "message": "Fatura já foi removida.", "details": []},
                status=400,
            )
        invoice.soft_delete()
        return Response({"message": "Fatura removida com sucesso."}, status=200)


@extend_schema(tags=["Admin — Metrics"])
class AdminMRRMetricsView(APIView):
    """
    GET /api/v1/billing/metrics/mrr/
    Platform-wide MRR, ARR, churn and monthly revenue trend.
    Admin only.
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="MRR, ARR e tendência de receita mensal", responses={200: MRRMetricsSerializer}
    )
    def get(self, request: Request) -> Response:
        from apps.billing.queries import get_mrr_metrics

        data = get_mrr_metrics()
        data["mrr"] = float(data["mrr"])
        data["arr"] = float(data["arr"])
        for row in data["monthly_revenue"]:
            row["revenue"] = float(row["revenue"])
        for row in data.get("revenue_by_plan", []):
            row["revenue"] = float(row["revenue"])
        return Response(data)


@extend_schema(tags=["Admin — Metrics"])
class AdminAPIUsageMetricsView(APIView):
    """
    GET /api/v1/billing/metrics/api-usage/
    Per-customer API call usage vs quota. Admin only.
    Supports optional ?customer_id= filter.
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Uso de API por customer",
        parameters=[OpenApiParameter("customer_id", str, description="Filtrar por customer UUID")],
        responses={200: APIUsageRowSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        from apps.licensing.models import LicenseQuota

        qs = LicenseQuota.objects.select_related("customer").order_by("-used_api_calls")
        if customer_id := request.query_params.get("customer_id"):
            qs = qs.filter(customer_id=customer_id)

        rows = [
            {
                "customer_id": str(q.customer_id),
                "company_name": q.customer.company_name,
                "used_api_calls": q.used_api_calls,
                "max_api_calls": q.max_api_calls,
                "usage_pct": round(q.used_api_calls / q.max_api_calls * 100, 1)
                if q.max_api_calls
                else 0,
                "reset_at": q.reset_at,
            }
            for q in qs
        ]
        return Response(rows)
