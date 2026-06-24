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
        ser = ProductWriteSerializer(product, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ProductSerializer(product).data)

    @extend_schema(summary="Desativar produto (soft delete)", responses={204: None})
    def delete(self, request: Request, pk: str) -> Response:
        product = self._get_product(pk)
        self._check_no_active_subscriptions(product)
        product.is_active = False
        product.save(update_fields=["is_active", "updated_at"])
        return Response(status=204)

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
