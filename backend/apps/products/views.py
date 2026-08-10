from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Pricing, Product, ServiceComponent
from apps.products.serializers import (
    PricingSerializer,
    ProductSerializer,
    ProductWriteSerializer,
    ServiceComponentSerializer,
)


@extend_schema(tags=["Products — Catálogo Público"])
class ActiveServiceSlugsView(APIView):
    """
    Só os slugs ativos — pra checagens internas de alta frequência (frontend
    consulta isso a cada request de página de serviço, via middleware, pra
    decidir se um serviço desativado deve virar 404 na hora — ver
    frontend/src/lib/active-services.ts). Sem throttle de propósito, mesmo
    padrão do HealthCheckView: é tráfego servidor-a-servidor, não abuso de
    usuário anônimo. Reaproveitar ProductCatalogView (que tem AnonRateThrottle
    padrão, 200/dia) pra isso esgotava a cota rapidinho — confirmado ao vivo,
    o middleware sozinho estourou em minutos de teste.
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = []

    @extend_schema(
        summary="Slugs de produtos ativos (público, sem throttle)",
        responses={200: None},
    )
    def get(self, request: Request) -> Response:
        slugs = list(Product.objects.filter(is_active=True).values_list("slug", flat=True))
        return Response(slugs)


@extend_schema(tags=["Products — Catálogo Público"])
class ProductCatalogView(APIView):
    """Public read-only product listing for clients to browse before subscribing."""

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        summary="Catálogo de produtos ativos (público, sem autenticação)",
        responses={200: ProductSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = (
            Product.objects.filter(is_active=True)
            .prefetch_related("components", "pricings")
            .order_by("name")
        )
        return Response(ProductSerializer(qs, many=True).data)


@extend_schema(tags=["Admin — Products"])
class ProductListCreateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="admin_products_list",
        summary="Listar todos os produtos",
        responses={200: ProductSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = Product.objects.prefetch_related("components", "pricings").order_by("name")
        return Response(ProductSerializer(qs, many=True).data)

    @extend_schema(
        summary="Criar novo produto",
        request=ProductWriteSerializer,
        responses={201: ProductSerializer},
    )
    def post(self, request: Request) -> Response:
        ser = ProductWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        product = ser.save()
        return Response(ProductSerializer(product).data, status=201)


@extend_schema(tags=["Admin — Products"])
class ProductDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get_product(self, pk: str) -> Product:
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Product.objects.prefetch_related("components", "pricings"), pk=pk)

    @extend_schema(summary="Detalhe de um produto", responses={200: ProductSerializer})
    def get(self, request: Request, pk: str) -> Response:
        return Response(ProductSerializer(self._get_product(pk)).data)

    @extend_schema(
        summary="Atualizar produto",
        request=ProductWriteSerializer,
        responses={200: ProductSerializer},
    )
    def patch(self, request: Request, pk: str) -> Response:
        product = self._get_product(pk)
        deactivating = (
            "is_active" in request.data and not request.data["is_active"] and product.is_active
        )
        if deactivating:
            self._check_no_active_subscriptions(product)
        was_active = product.is_active
        ser = ProductWriteSerializer(product, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        if product.is_active != was_active:
            self._revalidate_public_pages(product.slug)
        return Response(ProductSerializer(product).data)

    @extend_schema(summary="Desativar produto (soft delete)", responses={204: None})
    def delete(self, request: Request, pk: str) -> Response:
        product = self._get_product(pk)
        self._check_no_active_subscriptions(product)
        was_active = product.is_active
        product.is_active = False
        product.save(update_fields=["is_active", "updated_at"])
        if was_active:
            self._revalidate_public_pages(product.slug)
        return Response(status=204)

    @staticmethod
    def _revalidate_public_pages(slug: str) -> None:
        # Reaproveita a mesma task do app cms (post_save de ServicePage já
        # dispara nela) — ligar/desligar disponibilidade também precisa
        # purgar o ISR na hora, senão o site fica até 60s (ou indefinidamente,
        # se a página não receber outra visita nesse meio tempo — o
        # stale-while-revalidate só regenera na próxima requisição àquele
        # path específico) mostrando um serviço que acabou de ser
        # desativado. Achado testando ao vivo: /servicos atualizou rápido,
        # mas / e /servicos/<slug> ficaram em cache stale sem essa chamada.
        from apps.cms.tasks import revalidate_service_page

        revalidate_service_page.delay(slug)

    @staticmethod
    def _check_no_active_subscriptions(product: Product) -> None:
        from apps.subscriptions.models import Subscription

        count = Subscription.objects.filter(
            product=product,
            status__in=[Subscription.Status.ACTIVE, Subscription.Status.GRACE_PERIOD],
        ).count()
        if count:
            raise ValidationError(
                {
                    "is_active": (
                        f"Não é possível desativar: {count} assinatura(s) ativa(s) neste produto. "
                        "Cancele ou migre as assinaturas primeiro."
                    )
                }
            )


@extend_schema(tags=["Admin — Products"])
class ServiceComponentListCreateView(APIView):
    permission_classes = [IsAdminUser]

    def _get_product(self, pk: str) -> Product:
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Product, pk=pk)

    @extend_schema(
        summary="Listar componentes de serviço do produto",
        responses={200: ServiceComponentSerializer(many=True)},
    )
    def get(self, request: Request, product_pk: str) -> Response:
        qs = ServiceComponent.objects.filter(product_id=product_pk)
        return Response(ServiceComponentSerializer(qs, many=True).data)

    @extend_schema(
        summary="Adicionar componente de serviço ao produto",
        request=ServiceComponentSerializer,
        responses={201: ServiceComponentSerializer},
    )
    def post(self, request: Request, product_pk: str) -> Response:
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError

        product = self._get_product(product_pk)
        ser = ServiceComponentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            component = ser.save(product=product)
        except IntegrityError as exc:
            raise ValidationError(
                {"service_key": "Este serviço já está vinculado a este produto."}
            ) from exc
        return Response(ServiceComponentSerializer(component).data, status=201)


@extend_schema(tags=["Admin — Products"])
class PricingListCreateView(APIView):
    permission_classes = [IsAdminUser]

    def _get_product(self, pk: str) -> Product:
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Product, pk=pk)

    @extend_schema(
        summary="Listar pricings do produto", responses={200: PricingSerializer(many=True)}
    )
    def get(self, request: Request, product_pk: str) -> Response:
        qs = Pricing.objects.filter(product_id=product_pk)
        return Response(PricingSerializer(qs, many=True).data)

    @extend_schema(
        summary="Criar pricing para o produto",
        request=PricingSerializer,
        responses={201: PricingSerializer},
    )
    def post(self, request: Request, product_pk: str) -> Response:
        product = self._get_product(product_pk)
        ser = PricingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        pricing = ser.save(product=product)
        return Response(PricingSerializer(pricing).data, status=201)


@extend_schema(tags=["Admin — Products"])
class PricingDetailView(APIView):
    """
    Faltava esta view — o frontend (PricingManagerModal) já chamava
    PATCH .../pricings/<pricing_pk>/ pra editar uma precificação existente,
    mas só existia list+create em PricingListCreateView. Toda tentativa de
    editar um pricing batia 404. Achado auditando o backoffice.
    """

    permission_classes = [IsAdminUser]

    def _get_pricing(self, product_pk: str, pricing_pk: str) -> Pricing:
        from django.shortcuts import get_object_or_404

        return get_object_or_404(Pricing, pk=pricing_pk, product_id=product_pk)

    @extend_schema(
        summary="Atualizar pricing do produto",
        request=PricingSerializer,
        responses={200: PricingSerializer},
    )
    def patch(self, request: Request, product_pk: str, pricing_pk: str) -> Response:
        from django.db import IntegrityError

        pricing = self._get_pricing(product_pk, pricing_pk)
        ser = PricingSerializer(pricing, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            ser.save()
        except IntegrityError as exc:
            raise ValidationError(
                {
                    "billing_cycle": "Já existe uma precificação com este ciclo de cobrança neste produto."
                }
            ) from exc
        return Response(PricingSerializer(pricing).data)
