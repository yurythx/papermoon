import logging

from django.db import IntegrityError
from django.utils.text import slugify
from drf_spectacular.utils import OpenApiParameter, extend_schema
import requests
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.utils import log_action
from apps.provisioning.keycloak import (
    KeycloakClientAlreadyExistsError,
    KeycloakConnectionUnavailableError,
    KeycloakProvisioner,
)
from apps.subscriptions.commands import (
    CancelSubscriptionCommand,
    ChangeSubscriptionPlanCommand,
    ReactivateSubscriptionCommand,
    compute_proration,
)
from apps.subscriptions.keycloak_guide import (
    build_integration_guide,
    render_code_snippet,
    resolve_endpoints,
    resolve_keycloak_context,
)
from apps.subscriptions.keycloak_integration_content import DEFAULT_SCOPES, LANGUAGE_PACKS
from apps.subscriptions.models import KeycloakClientIntegration, Subscription
from apps.subscriptions.repositories import DjangoLicenseRepository
from apps.subscriptions.serializers import LicenseClientSerializer, SubscriptionSerializer
from shared.schemas import (
    ChangePlanRequestSerializer,
    KeycloakIntegrationCreateRequestSerializer,
    KeycloakIntegrationCreateResponseSerializer,
    KeycloakIntegrationGuideResponseSerializer,
    KeycloakIntegrationListResponseSerializer,
    KeycloakIntegrationSecretResponseSerializer,
    SubscribeRequestSerializer,
    SuspendReasonRequestSerializer,
    ValidateLicenseResponseSerializer,
)
from shared.throttling import KeycloakClientCreateRateThrottle

logger = logging.getLogger(__name__)


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


@extend_schema(tags=["Client — Assinaturas"])
class ClientKeycloakIntegrationGuideView(APIView):
    """
    Gera um guia de integração OIDC (URLs + snippet de código) pro sistema do
    cliente se conectar ao realm Keycloak provisionado pra ele. Só leitura —
    não cria nada no Keycloak nem salva nada aqui. Pra criar um client de
    verdade, ver ClientKeycloakIntegrationListCreateView abaixo. Ver também
    apps/subscriptions/keycloak_guide.py e keycloak_integration_content.py.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="client_keycloak_integration_guide",
        summary="Gerar guia de integração Keycloak",
        description=(
            "Devolve issuer/URLs/scopes reais do realm do cliente (com discovery "
            "confirmado quando possível) mais um snippet de código pronto pra "
            "colar, na stack escolhida. Se o PaperMoon não tem uma conexão "
            "central ativa com o Keycloak, ou se o cliente não tem um "
            "ServiceAccess 'keycloak' ativo, devolve {'available': false, "
            "'reason': ...} em vez de erro."
        ),
        parameters=[
            OpenApiParameter(
                "language",
                str,
                OpenApiParameter.QUERY,
                required=True,
                enum=list(LANGUAGE_PACKS),
            ),
            OpenApiParameter("app_name", str, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("base_url", str, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("redirect_path", str, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: KeycloakIntegrationGuideResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        customer = _customer_from_request(request)

        language = request.query_params.get("language", "")
        if language not in LANGUAGE_PACKS:
            raise ValidationError({"language": f"Deve ser um de: {', '.join(LANGUAGE_PACKS)}"})

        base_url = request.query_params.get("base_url", "").strip()
        if not base_url.startswith(("http://", "https://")):
            raise ValidationError({"base_url": "Informe uma URL http(s) completa."})

        app_name = request.query_params.get("app_name", "").strip() or "minha-aplicacao"
        redirect_path = request.query_params.get("redirect_path", "").strip() or None

        guide = build_integration_guide(
            customer,
            language=language,
            app_name=app_name,
            base_url=base_url,
            redirect_path=redirect_path,
        )
        return Response(guide)


def _keycloak_integrations_queryset(customer):
    """Isolamento de tenant: só integrações de ServiceAccess 'keycloak' que
    pertencem a uma license deste customer — mesmo raciocínio de
    DjangoLicenseRepository.get_for_customer."""
    return KeycloakClientIntegration.objects.filter(
        service_access__license__customer=customer,
        service_access__service_key="keycloak",
    )


def _serialize_keycloak_integration(integration: KeycloakClientIntegration) -> dict:
    return {
        "id": integration.id,
        "client_id": integration.client_id,
        "realm": integration.realm,
        "app_name": integration.app_name,
        "base_url": integration.base_url,
        "redirect_uri": integration.redirect_uri,
        "language": integration.language,
        "public_client": integration.public_client,
        "created_at": integration.created_at,
    }


# Mensagem única pro cliente final independente do motivo real — não faz
# sentido expor "o PaperMoon ainda não configurou o Keycloak dele" como se
# fosse um problema do plano do cliente. `reason` continua distinto na
# resposta (e nos logs) pra suporte diagnosticar.
_UNAVAILABLE_MESSAGE = (
    "Integração com o Keycloak ainda não está disponível para sua conta. "
    "Fale com o suporte do PaperMoon."
)


@extend_schema(tags=["Client — Assinaturas"])
class ClientKeycloakIntegrationListCreateView(APIView):
    """
    GET: lista as integrações Keycloak (clients OIDC) já criadas de verdade
    pra este cliente, mais o status de disponibilidade da funcionalidade.

    POST: cria um client OIDC DE VERDADE no realm do cliente via Admin REST
    API do Keycloak (apps.provisioning.keycloak.KeycloakProvisioner) e
    devolve client_id/client_secret reais. Pré-requisito checado nesta ordem:
    (1) o PaperMoon precisa ter uma conexão central ativa com o Keycloak
    (apps.provisioning.keycloak_config — configurável em backoffice/settings),
    (2) o cliente precisa ter um ServiceAccess 'keycloak' ativo. Nunca cria
    nada localmente sem o client existir de verdade no Keycloak primeiro.
    """

    permission_classes = [IsAuthenticated]

    def get_throttles(self) -> list:
        if self.request.method == "POST":
            return [KeycloakClientCreateRateThrottle()]
        return super().get_throttles()

    @extend_schema(
        operation_id="client_keycloak_integrations_list",
        summary="Listar minhas integrações Keycloak",
        responses={200: KeycloakIntegrationListResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        customer = _customer_from_request(request)
        _ctx, reason = resolve_keycloak_context(customer)
        integrations = _keycloak_integrations_queryset(customer).order_by("-created_at")
        return Response(
            {
                "available": reason is None,
                "reason": reason,
                "integrations": [_serialize_keycloak_integration(i) for i in integrations],
            }
        )

    @extend_schema(
        operation_id="client_keycloak_integrations_create",
        summary="Criar integração Keycloak (client OIDC de verdade)",
        request=KeycloakIntegrationCreateRequestSerializer,
        responses={201: KeycloakIntegrationCreateResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        customer = _customer_from_request(request)

        language = (request.data.get("language") or "").strip()
        if language not in LANGUAGE_PACKS:
            raise ValidationError({"language": f"Deve ser um de: {', '.join(LANGUAGE_PACKS)}"})

        base_url = (request.data.get("base_url") or "").strip()
        if not base_url.startswith(("http://", "https://")):
            raise ValidationError({"base_url": "Informe uma URL http(s) completa."})
        base_url = base_url.rstrip("/")

        app_name = (request.data.get("app_name") or "").strip() or "minha-aplicacao"
        redirect_path = (request.data.get("redirect_path") or "").strip() or None

        ctx, reason = resolve_keycloak_context(customer)
        if ctx is None:
            # platform_not_configured é um problema da plataforma (nada que o
            # cliente fez) — 409. no_service_access é falta de direito de
            # acesso deste cliente ao serviço — 403.
            status_code = 409 if reason == "platform_not_configured" else 403
            return Response(
                {"code": reason, "message": _UNAVAILABLE_MESSAGE, "details": []},
                status=status_code,
            )

        pack = LANGUAGE_PACKS[language]
        public_client = pack["public_client"]
        resolved_redirect_path = redirect_path or pack.get(
            "default_redirect_path", "/auth/callback"
        )
        redirect_uri = base_url + resolved_redirect_path
        client_id = slugify(app_name) or "minha-aplicacao"

        if _keycloak_integrations_queryset(customer).filter(client_id=client_id).exists():
            return Response(
                {
                    "code": "client_already_exists",
                    "message": (
                        f"Já existe uma integração com o identificador '{client_id}' — "
                        "escolha outro nome de aplicação."
                    ),
                    "details": [],
                },
                status=409,
            )

        provisioner = KeycloakProvisioner()
        try:
            result = provisioner.create_oidc_client(
                realm=ctx.realm,
                client_id=client_id,
                name=app_name,
                redirect_uris=[redirect_uri],
                web_origins=[base_url],
                public_client=public_client,
                base_url=base_url,
            )
        except KeycloakConnectionUnavailableError:
            return Response(
                {"code": "platform_not_configured", "message": _UNAVAILABLE_MESSAGE, "details": []},
                status=409,
            )
        except KeycloakClientAlreadyExistsError:
            return Response(
                {
                    "code": "client_already_exists",
                    "message": (
                        f"Já existe um client '{client_id}' nesse realm do Keycloak — "
                        "escolha outro nome de aplicação."
                    ),
                    "details": [],
                },
                status=409,
            )
        except requests.RequestException as exc:
            logger.warning("Falha ao criar client OIDC no Keycloak: %s", exc)
            return Response(
                {
                    "code": "keycloak_unreachable",
                    "message": "Não foi possível conectar ao Keycloak agora. Tente novamente em instantes.",
                    "details": [],
                },
                status=502,
            )

        try:
            integration = KeycloakClientIntegration.objects.create(
                service_access=ctx.service_access,
                client_id=result["client_id"],
                kc_uuid=result["kc_uuid"],
                realm=ctx.realm,
                app_name=app_name,
                base_url=base_url,
                redirect_uri=redirect_uri,
                language=language,
                public_client=public_client,
                created_by=request.user,
            )
        except IntegrityError:
            # Corrida rara: o client já foi criado no Keycloak (acima) mas a
            # linha local colidiu — o client fica órfão no Keycloak (sem
            # tracking local); aceitável para este escopo, não crítico.
            return Response(
                {
                    "code": "client_already_exists",
                    "message": (
                        f"Já existe uma integração com o identificador '{client_id}' — "
                        "escolha outro nome de aplicação."
                    ),
                    "details": [],
                },
                status=409,
            )

        log_action(
            "keycloak_client_integration.created",
            "KeycloakClientIntegration",
            str(integration.pk),
            user=request.user,
            request=request,
            changes={
                "client_id": integration.client_id,
                "realm": integration.realm,
                "language": integration.language,
                "public_client": integration.public_client,
            },
        )

        endpoints, verified = resolve_endpoints(ctx.issuer)
        code_snippet = render_code_snippet(
            language=language,
            issuer=ctx.issuer,
            client_id=integration.client_id,
            redirect_uri=redirect_uri,
            redirect_path=resolved_redirect_path,
            base_url=base_url,
            endpoints=endpoints,
            client_secret=result["client_secret"],
            scopes=DEFAULT_SCOPES,
        )

        return Response(
            {
                "id": integration.id,
                "client_id": integration.client_id,
                "client_secret": result["client_secret"],
                "public_client": public_client,
                "verified": verified,
                "issuer": ctx.issuer,
                "authorization_endpoint": endpoints["authorization_endpoint"],
                "token_endpoint": endpoints["token_endpoint"],
                "userinfo_endpoint": endpoints["userinfo_endpoint"],
                "jwks_uri": endpoints["jwks_uri"],
                "end_session_endpoint": endpoints["end_session_endpoint"],
                "redirect_uri": redirect_uri,
                "scopes": DEFAULT_SCOPES,
                "language": language,
                "package": pack["package"],
                "install_command": pack["install_command"],
                "steps": pack["steps"],
                "code_snippet": code_snippet,
            },
            status=201,
        )


@extend_schema(tags=["Client — Assinaturas"])
class ClientKeycloakIntegrationSecretView(APIView):
    """Rebusca o client_secret fresco no Keycloak — nunca fica persistido
    localmente (ver KeycloakClientIntegration), então toda visualização passa
    por uma chamada real ao Admin REST API."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="client_keycloak_integration_secret",
        summary="Ver client_secret de uma integração",
        description="400 se o client for público (PKCE, sem secret). 404 se a integração não é sua.",
        responses={200: KeycloakIntegrationSecretResponseSerializer},
    )
    def get(self, request: Request, pk: str) -> Response:
        from django.shortcuts import get_object_or_404

        customer = _customer_from_request(request)
        integration = get_object_or_404(_keycloak_integrations_queryset(customer), pk=pk)

        if integration.public_client:
            raise ValidationError(
                {"detail": "Este client é público (PKCE) — não tem client_secret."}
            )

        _ctx, reason = resolve_keycloak_context(customer)
        if reason is not None:
            status_code = 409 if reason == "platform_not_configured" else 403
            return Response(
                {"code": reason, "message": _UNAVAILABLE_MESSAGE, "details": []},
                status=status_code,
            )

        provisioner = KeycloakProvisioner()
        try:
            client_secret = provisioner.get_client_secret(
                realm=integration.realm, kc_uuid=integration.kc_uuid
            )
        except KeycloakConnectionUnavailableError:
            return Response(
                {"code": "platform_not_configured", "message": _UNAVAILABLE_MESSAGE, "details": []},
                status=409,
            )
        except requests.RequestException as exc:
            logger.warning("Falha ao rebuscar client_secret no Keycloak: %s", exc)
            return Response(
                {
                    "code": "keycloak_unreachable",
                    "message": "Não foi possível conectar ao Keycloak agora. Tente novamente em instantes.",
                    "details": [],
                },
                status=502,
            )

        log_action(
            "keycloak_client_integration.secret_viewed",
            "KeycloakClientIntegration",
            str(integration.pk),
            user=request.user,
            request=request,
            changes={"client_id": integration.client_id},
        )
        return Response({"client_secret": client_secret})
