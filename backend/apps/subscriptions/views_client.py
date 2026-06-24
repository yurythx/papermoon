from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.utils import log_action
from apps.subscriptions.commands import (
    CancelSubscriptionCommand,
    ChangeSubscriptionPlanCommand,
    ReactivateSubscriptionCommand,
    compute_proration,
)
from apps.subscriptions.models import Subscription
from apps.subscriptions.repositories import DjangoLicenseRepository
from apps.subscriptions.serializers import LicenseClientSerializer, SubscriptionSerializer
from shared.schemas import (
    ChangePlanRequestSerializer,
    SubscribeRequestSerializer,
    SuspendReasonRequestSerializer,
    ValidateLicenseResponseSerializer,
)


def _customer_from_request(request):
    from apps.customers.models import CustomerProfile

    profile = CustomerProfile.objects.filter(user=request.user).select_related("customer").first()
    if not profile:
        raise PermissionDenied("No customer profile found.")
    return profile.customer


@extend_schema(tags=["Client — Assinaturas"])
class ClientSubscriptionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="client_subscriptions_list",
        summary="Listar minhas assinaturas",
        responses={200: SubscriptionSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        from apps.subscriptions.queries import list_client_subscriptions

        customer = _customer_from_request(request)
        qs = list_client_subscriptions(customer.id)
        return Response(SubscriptionSerializer(qs, many=True).data)

    @extend_schema(
        summary="Assinar produto (self-service)",
        request=SubscribeRequestSerializer,
        responses={201: SubscriptionSerializer},
    )
    def post(self, request: Request) -> Response:
        """
        Self-service subscription creation.
        Customer browses active products and subscribes to one.
        Prevents duplicate active subscriptions for the same product.
        """
        from apps.products.models import Pricing, Product
        from apps.subscriptions.commands import CreateSubscriptionCommand

        customer = _customer_from_request(request)

        product_id = request.data.get("product_id")
        pricing_id = request.data.get("pricing_id")

        if not product_id or not pricing_id:
            raise ValidationError({"detail": "product_id and pricing_id are required."})

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist as exc:
            raise ValidationError({"product_id": "Product not found or inactive."}) from exc

        try:
            pricing = Pricing.objects.get(pk=pricing_id, product=product, is_active=True)
        except Pricing.DoesNotExist as exc:
            raise ValidationError(
                {"pricing_id": "Pricing not found or inactive for this product."}
            ) from exc

        # Prevent duplicate active subscriptions for the same product
        duplicate = Subscription.objects.filter(
            customer=customer,
            product=product,
            status__in=[
                Subscription.Status.TRIAL,
                Subscription.Status.ACTIVE,
                Subscription.Status.GRACE_PERIOD,
            ],
        ).exists()
        if duplicate:
            raise ValidationError(
                {"product_id": "You already have an active subscription for this product."}
            )

        subscription = CreateSubscriptionCommand().execute(
            customer_id=customer.id,
            product_id=product.id,
            pricing_id=pricing.id,
        )
        return Response(SubscriptionSerializer(subscription).data, status=201)


@extend_schema(tags=["Client — Assinaturas"])
class ClientSubscriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Detalhe de uma assinatura do tenant", responses={200: SubscriptionSerializer}
    )
    def get(self, request: Request, pk: str) -> Response:
        from rest_framework.exceptions import NotFound

        from apps.subscriptions.queries import get_client_subscription

        customer = _customer_from_request(request)
        try:
            subscription = get_client_subscription(pk, customer.id)
        except NotFound:
            return Response(
                {"code": "not_found", "message": "Assinatura não encontrada.", "details": []},
                status=404,
            )
        return Response(SubscriptionSerializer(subscription).data)


@extend_schema(tags=["Client — Assinaturas"])
class ClientChangePlanPreviewView(APIView):
    """
    GET /api/v1/client/subscriptions/<pk>/change-plan-preview/?pricing_id=xxx

    Returns the prorated amount the customer will be charged when upgrading
    mid-cycle. Does NOT execute the plan change — safe to call on selection.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Preview de proration para troca de plano",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "proration_amount": {"type": "string"},
                    "has_proration": {"type": "boolean"},
                },
            }
        },
    )
    def get(self, request: Request, pk: str) -> Response:
        from django.shortcuts import get_object_or_404
        from django.utils import timezone

        from apps.products.models import Pricing

        customer = _customer_from_request(request)
        sub = get_object_or_404(
            Subscription.objects.select_related("pricing"),
            pk=pk,
            customer=customer,
        )

        new_pricing_id = request.query_params.get("pricing_id")
        if not new_pricing_id:
            raise ValidationError({"pricing_id": "This field is required."})

        try:
            new_pricing = Pricing.objects.get(pk=new_pricing_id, product=sub.product)
        except Pricing.DoesNotExist as exc:
            raise ValidationError({"pricing_id": "Pricing not found for this product."}) from exc

        proration = compute_proration(sub, sub.pricing, new_pricing, timezone.now())
        return Response(
            {
                "proration_amount": str(proration),
                "has_proration": proration > 0,
            }
        )


@extend_schema(tags=["Client — Assinaturas"])
class ClientSubscriptionChangePlanView(APIView):
    """
    POST /api/v1/client/subscriptions/<pk>/change-plan/
    Allows a customer to upgrade or downgrade their own subscription.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Upgrade/downgrade de plano (self-service)",
        request=ChangePlanRequestSerializer,
        responses={201: SubscriptionSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        from django.shortcuts import get_object_or_404

        customer = _customer_from_request(request)
        sub = get_object_or_404(Subscription, pk=pk, customer=customer)

        new_pricing_id = request.data.get("pricing_id")
        if not new_pricing_id:
            raise ValidationError({"pricing_id": "This field is required."})

        try:
            new_sub = ChangeSubscriptionPlanCommand().execute(sub.id, new_pricing_id)
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


@extend_schema(tags=["Client — Assinaturas"])
class ClientSubscriptionReactivateView(APIView):
    """
    POST /api/v1/client/subscriptions/<pk>/reactivate/
    Self-service reactivation of a suspended subscription.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Reativar assinatura suspensa (self-service)",
        request=None,
        responses={200: SubscriptionSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        from django.shortcuts import get_object_or_404

        customer = _customer_from_request(request)
        sub = get_object_or_404(Subscription, pk=pk, customer=customer)

        try:
            reactivated = ReactivateSubscriptionCommand().execute(sub.id)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(SubscriptionSerializer(reactivated).data)


@extend_schema(tags=["Client — Assinaturas"])
class ClientSubscriptionCancelView(APIView):
    """
    POST /api/v1/client/subscriptions/<pk>/cancel/
    Self-service cancellation. Allowed from any non-cancelled status.
    Irreversible — client must re-subscribe via catalog.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Cancelar assinatura (self-service)",
        request=SuspendReasonRequestSerializer,
        responses={200: SubscriptionSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        from django.shortcuts import get_object_or_404

        customer = _customer_from_request(request)
        sub = get_object_or_404(Subscription, pk=pk, customer=customer)

        if sub.status == Subscription.Status.CANCELLED:
            raise ValidationError({"detail": "A assinatura já está cancelada."})

        reason = request.data.get("reason", "client_requested")
        cancelled = CancelSubscriptionCommand().execute(sub.id, reason=reason)
        return Response(SubscriptionSerializer(cancelled).data)


def _license_repo() -> DjangoLicenseRepository:
    return DjangoLicenseRepository()


@extend_schema(tags=["Client — Licenças"])
class ClientLicenseListView(APIView):
    """
    GET /api/v1/client/licenses/

    Returns every license owned by the authenticated customer, ordered
    newest-first. Each item includes product context, days_remaining and
    the full list of provisioned services so the frontend can render the
    "My Products" page without extra round-trips.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="client_licenses_list",
        summary="Listar minhas licenças",
        description=(
            "Retorna todas as licenças do tenant autenticado com contexto de produto, "
            "dias restantes e serviços provisionados. Não requer parâmetros."
        ),
        responses={200: LicenseClientSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        customer = _customer_from_request(request)
        licenses = _license_repo().list_by_customer(customer.id)
        return Response(LicenseClientSerializer(licenses, many=True).data)


@extend_schema(tags=["Client — Licenças"])
class ClientLicenseDetailView(APIView):
    """
    GET /api/v1/client/licenses/<pk>/

    Returns a single license. Only accessible if the license belongs to
    the authenticated customer — guarantees tenant isolation at the
    repository layer, not in the view.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Detalhe de uma licença",
        description="Retorna a licença com chave, validade, produto e todos os serviços provisionados.",
        responses={200: LicenseClientSerializer},
    )
    def get(self, request: Request, pk: str) -> Response:
        customer = _customer_from_request(request)
        license_obj = _license_repo().get_for_customer(pk, customer.id)
        return Response(LicenseClientSerializer(license_obj).data)


@extend_schema(tags=["Licensing"])
class ClientLicenseValidateView(APIView):
    """
    Public endpoint: GET /api/v1/subscriptions/validate-license/?key=xxx
    Returns license validity + service access status.
    Cached in Redis for 60 seconds.
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Validar licença (público)",
        description="Verifica se uma license key é válida e quais serviços estão ativos. Cacheado 60s no Redis.",
        responses={200: ValidateLicenseResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        from django.core.cache import cache

        from apps.subscriptions.models import License

        key = request.query_params.get("key", "").strip()
        if not key:
            return Response({"valid": False, "reason": "key_required"}, status=400)

        import hashlib

        cache_key = f"license:{hashlib.sha256(key.encode()).hexdigest()[:32]}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        try:
            license_obj = (
                License.objects.select_related("subscription__product")
                .prefetch_related("service_accesses")
                .get(key=key)
            )
        except License.DoesNotExist:
            result = {"valid": False, "reason": "not_found"}
            cache.set(cache_key, result, timeout=60)
            return Response(result, status=404)

        is_valid = license_obj.is_valid()
        result = {
            "valid": is_valid,
            "status": license_obj.status,
            "valid_until": license_obj.valid_until.isoformat(),
            "product": license_obj.subscription.product.slug,
            "services": {sa.service_key: sa.status for sa in license_obj.service_accesses.all()},
        }
        cache.set(cache_key, result, timeout=60)
        return Response(result)
