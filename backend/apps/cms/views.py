from __future__ import annotations

from django.db import models
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cms.models import ServiceImage, ServicePage
from apps.cms.repositories import DjangoCMSRepository
from apps.cms.serializers import (
    ServiceImageAdminSerializer,
    ServicePageAdminListSerializer,
    ServicePageAdminSerializer,
    ServicePageSerializer,
    ServiceSlugSerializer,
)
from apps.cms.tasks import revalidate_service_page
from apps.products.models import Product
from shared.public_urls import build_public_media_url


@extend_schema(tags=["CMS — Public"])
class ServicePageDetailView(APIView):
    """GET /api/v1/cms/services/{slug}/ — full page content, no auth required."""

    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        summary="Conteúdo CMS da página de serviço",
        responses={200: ServicePageSerializer, 404: None},
    )
    def get(self, request: Request, slug: str) -> Response:
        repo = DjangoCMSRepository()
        page = repo.get_page_by_slug(slug)
        if page is None:
            raise NotFound(f"Página CMS não encontrada para o slug '{slug}'.")
        return Response(ServicePageSerializer(page, context={"request": request}).data)


@extend_schema(tags=["CMS — Public"])
class ServiceSlugListView(APIView):
    """GET /api/v1/cms/services/ — list of slugs with CMS content (for generateStaticParams)."""

    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        summary="Lista slugs com conteúdo CMS",
        responses={200: ServiceSlugSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        return Response(DjangoCMSRepository().list_slugs())


@extend_schema(tags=["CMS — Admin"])
class RevalidateServicePageView(APIView):
    """POST /api/v1/admin/cms/revalidate/{slug}/ — trigger Next.js ISR revalidation."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Dispara revalidação ISR no Next.js para o serviço",
        responses={200: None},
    )
    def post(self, request: Request, slug: str) -> Response:
        revalidate_service_page.delay(slug)
        return Response({"scheduled": True, "slug": slug})


@extend_schema(tags=["CMS — Admin"])
class ServicePageAdminListView(APIView):
    """GET /api/v1/admin/cms/pages/ — all products + whether they have a CMS page."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Lista todos os produtos com status de página CMS",
        responses={200: ServicePageAdminListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        products = (
            Product.objects.prefetch_related("cms_page").filter(is_active=True).order_by("name")
        )
        rows = []
        for product in products:
            page = getattr(product, "cms_page", None)
            rows.append(
                {
                    "slug": product.slug,
                    "product_name": product.name,
                    "has_page": page is not None,
                    "updated_at": page.updated_at if page else None,
                }
            )
        return Response(ServicePageAdminListSerializer(rows, many=True).data)


@extend_schema(tags=["CMS — Admin"])
class ServicePageAdminDetailView(APIView):
    """GET/PATCH /api/v1/admin/cms/pages/{slug}/ — read and edit a CMS page."""

    permission_classes = [IsAdminUser]

    def _get_or_create(self, slug: str) -> ServicePage:
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise NotFound(f"Produto com slug '{slug}' não encontrado.") from None
        page, _ = ServicePage.objects.prefetch_related(
            "responsibilities",
            "steps",
            "feature_groups__items",
            "faqs",
            "images",
        ).get_or_create(product=product)
        # Re-fetch with prefetch after potential creation
        return (
            ServicePage.objects.select_related("product")
            .prefetch_related(
                "responsibilities", "steps", "feature_groups__items", "faqs", "images"
            )
            .get(pk=page.pk)
        )

    @extend_schema(
        summary="Retorna dados completos de uma página CMS para edição",
        responses={200: ServicePageAdminSerializer},
    )
    def get(self, request: Request, slug: str) -> Response:
        page = self._get_or_create(slug)
        return Response(ServicePageAdminSerializer(page, context={"request": request}).data)

    @extend_schema(
        summary="Atualiza página CMS (substitui coleções aninhadas integralmente)",
        request=ServicePageAdminSerializer,
        responses={200: ServicePageAdminSerializer},
    )
    def patch(self, request: Request, slug: str) -> Response:
        page = self._get_or_create(slug)
        serializer = ServicePageAdminSerializer(
            page, data=request.data, partial=True, context={"request": request}
        )
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        serializer.save()

        revalidate_service_page.delay(slug)

        return Response(
            ServicePageAdminSerializer(
                ServicePage.objects.select_related("product")
                .prefetch_related(
                    "responsibilities", "steps", "feature_groups__items", "faqs", "images"
                )
                .get(pk=page.pk),
                context={"request": request},
            ).data
        )


@extend_schema(tags=["CMS — Admin"])
class ServicePageHeroUploadView(APIView):
    """POST /api/v1/admin/cms/pages/{slug}/hero/ — upload hero image (multipart).
    DELETE /api/v1/admin/cms/pages/{slug}/hero/ — remove hero image."""

    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def _get_page(self, slug: str) -> ServicePage:
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise NotFound(f"Produto '{slug}' não encontrado.") from None
        page, _ = ServicePage.objects.select_related("product").get_or_create(product=product)
        return page

    @extend_schema(summary="Faz upload da imagem hero de uma página CMS")
    def post(self, request: Request, slug: str) -> Response:
        page = self._get_page(slug)
        image_file = request.FILES.get("hero_image")
        if not image_file:
            raise ValidationError({"hero_image": "Arquivo de imagem obrigatório."})
        page.hero_image = image_file
        page.save()
        hero_url = build_public_media_url(page.hero_image.url if page.hero_image else None, request)
        return Response({"hero_image_url": hero_url})

    @extend_schema(summary="Remove a imagem hero de uma página CMS")
    def delete(self, request: Request, slug: str) -> Response:
        page = self._get_page(slug)
        if page.hero_image:
            page.hero_image.delete(save=True)
        return Response({"hero_image_url": None})


@extend_schema(tags=["CMS — Admin"])
class ServicePageGalleryView(APIView):
    """POST /api/v1/admin/cms/pages/{slug}/gallery/ — upload gallery image.
    DELETE /api/v1/admin/cms/pages/{slug}/gallery/{pk}/ — remove gallery image."""

    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]

    def _get_page(self, slug: str) -> ServicePage:
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise NotFound(f"Produto '{slug}' não encontrado.") from None
        page, _ = ServicePage.objects.select_related("product").get_or_create(product=product)
        return page

    @extend_schema(summary="Faz upload de imagem na galeria de uma página CMS")
    def post(self, request: Request, slug: str) -> Response:
        page = self._get_page(slug)
        image_file = request.FILES.get("image")
        if not image_file:
            raise ValidationError({"image": "Arquivo de imagem obrigatório."})
        last_order = page.images.aggregate(max_order=models.Max("order"))["max_order"] or 0
        image = ServiceImage.objects.create(
            page=page,
            file=image_file,
            alt=request.data.get("alt", ""),
            caption=request.data.get("caption", ""),
            order=last_order + 1,
        )
        return Response(
            ServiceImageAdminSerializer(image, context={"request": request}).data,
            status=201,
        )


@extend_schema(tags=["CMS — Admin"])
class ServicePageGalleryDeleteView(APIView):
    """DELETE /api/v1/admin/cms/pages/{slug}/gallery/{pk}/ — remove a specific gallery image."""

    permission_classes = [IsAdminUser]

    @extend_schema(summary="Remove imagem da galeria de uma página CMS")
    def delete(self, request: Request, slug: str, pk: int) -> Response:
        try:
            image = ServiceImage.objects.select_related("page__product").get(
                pk=pk, page__product__slug=slug
            )
        except ServiceImage.DoesNotExist:
            raise NotFound("Imagem não encontrada.") from None
        image.file.delete(save=False)
        image.delete()
        return Response(status=204)
