from __future__ import annotations

from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blog.models import BlogPost
from apps.blog.serializers import BlogPostAdminListSerializer, BlogPostAdminSerializer
from apps.cms.services import ImageProcessor, InvalidImageUploadError, validate_image_upload
from shared.public_urls import build_public_media_url
from shared.throttling import AdminWriteThrottle


@extend_schema(tags=["Blog — Admin"])
class BlogPostAdminListCreateView(APIView):
    """GET  /api/v1/admin/blog/  — all posts, any status.
    POST /api/v1/admin/blog/  — cria um post (status=draft por padrão, autor = usuário logado)."""

    permission_classes = [IsAdminUser]

    def get_throttles(self) -> list:
        if self.request.method == "POST":
            return [AdminWriteThrottle()]
        return super().get_throttles()

    @extend_schema(
        summary="Listar posts (admin — todos os status)",
        parameters=[
            OpenApiParameter("status", str, description="draft | published"),
            OpenApiParameter("page", int),
        ],
        responses={200: BlogPostAdminListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = (
            BlogPost.objects.select_related("author")
            .prefetch_related("tags")
            .order_by("-created_at")
        )
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(BlogPostAdminListSerializer(page, many=True).data)

    @extend_schema(
        summary="Criar post",
        request=BlogPostAdminSerializer,
        responses={201: BlogPostAdminSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = BlogPostAdminSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        return Response(
            BlogPostAdminSerializer(post, context={"request": request}).data, status=201
        )


@extend_schema(tags=["Blog — Admin"])
class BlogPostAdminDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/admin/blog/{id}/"""

    permission_classes = [IsAdminUser]

    def get_throttles(self) -> list:
        if self.request.method in ("PATCH", "DELETE"):
            return [AdminWriteThrottle()]
        return super().get_throttles()

    def _get_post(self, pk: str) -> BlogPost:
        try:
            return BlogPost.objects.select_related("author").prefetch_related("tags").get(pk=pk)
        except (BlogPost.DoesNotExist, ValueError):
            raise NotFound("Post não encontrado.") from None

    @extend_schema(summary="Detalhe de um post (admin)", responses={200: BlogPostAdminSerializer})
    def get(self, request: Request, pk: str) -> Response:
        return Response(
            BlogPostAdminSerializer(self._get_post(pk), context={"request": request}).data
        )

    @extend_schema(
        summary="Atualizar post (inclui publicar/despublicar via status)",
        request=BlogPostAdminSerializer,
        responses={200: BlogPostAdminSerializer},
    )
    def patch(self, request: Request, pk: str) -> Response:
        post = self._get_post(pk)
        serializer = BlogPostAdminSerializer(
            post, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            BlogPostAdminSerializer(
                BlogPost.objects.select_related("author").prefetch_related("tags").get(pk=post.pk),
                context={"request": request},
            ).data
        )

    @extend_schema(summary="Remover post", responses={204: None})
    def delete(self, request: Request, pk: str) -> Response:
        post = self._get_post(pk)
        if post.cover_image:
            post.cover_image.delete(save=False)
        post.delete()
        return Response(status=204)


@extend_schema(tags=["Blog — Admin"])
class BlogPostCoverUploadView(APIView):
    """POST   /api/v1/admin/blog/{id}/cover/ — upload da capa (multipart).
    DELETE /api/v1/admin/blog/{id}/cover/ — remove a capa."""

    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]
    throttle_classes = [AdminWriteThrottle]

    def _get_post(self, pk: str) -> BlogPost:
        try:
            return BlogPost.objects.get(pk=pk)
        except (BlogPost.DoesNotExist, ValueError):
            raise NotFound("Post não encontrado.") from None

    @extend_schema(summary="Faz upload da capa de um post")
    def post(self, request: Request, pk: str) -> Response:
        post = self._get_post(pk)
        image_file = request.FILES.get("cover_image")
        if not image_file:
            raise ValidationError({"cover_image": "Arquivo de imagem obrigatório."})
        try:
            validate_image_upload(image_file.content_type, image_file.size, image_file.read())
            image_file.seek(0)
        except InvalidImageUploadError as exc:
            raise ValidationError({"cover_image": str(exc)}) from exc
        post.cover_image = image_file
        post.save()
        cover_url = build_public_media_url(
            post.cover_image.url if post.cover_image else None, request
        )
        return Response({"cover_image_url": cover_url})

    @extend_schema(summary="Remove a capa de um post")
    def delete(self, request: Request, pk: str) -> Response:
        post = self._get_post(pk)
        if post.cover_image:
            post.cover_image.delete(save=True)
        return Response({"cover_image_url": None})


@extend_schema(tags=["Blog — Admin"])
class BlogPostBodyImageUploadView(APIView):
    """POST /api/v1/admin/blog/{id}/body-image/ — upload de imagem pra inserir
    no corpo em Markdown (`![alt](url)`, botão de imagem da toolbar).

    Sem model próprio (ao contrário da galeria do CMS — ServiceImage, ordenada,
    com alt/caption estruturados): o Markdown do post já é a única fonte de
    verdade de onde/quantas vezes cada imagem é usada, então isso aqui é só um
    arquivo em storage — o front recebe a URL e insere a sintaxe ele mesmo."""

    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser]
    throttle_classes = [AdminWriteThrottle]

    def _get_post(self, pk: str) -> BlogPost:
        try:
            return BlogPost.objects.get(pk=pk)
        except (BlogPost.DoesNotExist, ValueError):
            raise NotFound("Post não encontrado.") from None

    @extend_schema(summary="Faz upload de uma imagem pro corpo de um post")
    def post(self, request: Request, pk: str) -> Response:
        post = self._get_post(pk)
        image_file = request.FILES.get("image")
        if not image_file:
            raise ValidationError({"image": "Arquivo de imagem obrigatório."})
        data = image_file.read()
        try:
            validate_image_upload(image_file.content_type, image_file.size, data)
        except InvalidImageUploadError as exc:
            raise ValidationError({"image": str(exc)}) from exc

        webp_bytes = ImageProcessor.to_webp(data)
        path = default_storage.save(
            f"blog/body/{post.slug}/{uuid4().hex}.webp", ContentFile(webp_bytes)
        )
        image_url = build_public_media_url(default_storage.url(path), request)
        return Response({"image_url": image_url}, status=201)
