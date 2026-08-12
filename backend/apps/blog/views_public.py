from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blog.models import BlogPost
from apps.blog.serializers import BlogPostPublicDetailSerializer, BlogPostPublicListSerializer


@extend_schema(tags=["Blog — Public"])
class BlogPostListView(APIView):
    """GET /api/v1/blog/ — published posts only, paginated, no auth required."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Lista posts publicados do blog",
        parameters=[
            OpenApiParameter("page", int),
            OpenApiParameter("tag", str, description="Filtra por slug da tag"),
        ],
        responses={200: BlogPostPublicListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = (
            BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)
            .select_related("author")
            .prefetch_related("tags")
            .order_by("-published_at")
        )
        tag_slug = request.query_params.get("tag")
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            BlogPostPublicListSerializer(page, many=True, context={"request": request}).data
        )


@extend_schema(tags=["Blog — Public"])
class BlogPostDetailView(APIView):
    """GET /api/v1/blog/{slug}/ — a single published post. 404s for drafts
    too — a draft's slug leaking a 200 (even without listing it) would let
    anyone with the URL read unpublished content."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Detalhe de um post publicado",
        responses={200: BlogPostPublicDetailSerializer, 404: None},
    )
    def get(self, request: Request, slug: str) -> Response:
        try:
            post = (
                BlogPost.objects.select_related("author")
                .prefetch_related("tags")
                .get(slug=slug, status=BlogPost.Status.PUBLISHED)
            )
        except BlogPost.DoesNotExist:
            raise NotFound(f"Post '{slug}' não encontrado.") from None
        return Response(BlogPostPublicDetailSerializer(post, context={"request": request}).data)
