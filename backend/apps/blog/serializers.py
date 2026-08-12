from __future__ import annotations

from rest_framework import serializers

from apps.blog.models import BlogPost
from shared.public_urls import build_public_media_url


class BlogPostPublicListSerializer(serializers.ModelSerializer):
    """Card row for /blog — no body, keeps the listing payload light."""

    cover_image_url = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "slug",
            "title",
            "excerpt",
            "cover_image_url",
            "cover_image_alt",
            "author_name",
            "published_at",
        ]

    def get_cover_image_url(self, obj: BlogPost) -> str | None:
        request = self.context.get("request")
        return build_public_media_url(
            obj.cover_image.url if obj.cover_image else None, request=request
        )

    def get_author_name(self, obj: BlogPost) -> str:
        return obj.author.get_full_name() or obj.author.username


class BlogPostPublicDetailSerializer(BlogPostPublicListSerializer):
    class Meta(BlogPostPublicListSerializer.Meta):
        fields = [
            *BlogPostPublicListSerializer.Meta.fields,
            "body",
            "meta_title",
            "meta_description",
        ]


class BlogPostAdminSerializer(serializers.ModelSerializer):
    """Read + write serializer for the backoffice editor.

    Read-only image fields mirror ServicePageAdminSerializer's pattern —
    cover upload goes through its own multipart endpoint
    (BlogPostCoverUploadView), same reasoning as the CMS hero image.
    """

    cover_image_url = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "body",
            "cover_image_url",
            "cover_image_alt",
            "author",
            "author_name",
            "status",
            "published_at",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "cover_image_url",
            "author",
            "author_name",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def get_cover_image_url(self, obj: BlogPost) -> str | None:
        request = self.context.get("request")
        return build_public_media_url(
            obj.cover_image.url if obj.cover_image else None, request=request
        )

    def get_author_name(self, obj: BlogPost) -> str:
        return obj.author.get_full_name() or obj.author.username

    def update(self, instance: BlogPost, validated_data: dict) -> BlogPost:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.mark_published()
        instance.save()
        return instance


class BlogPostAdminListSerializer(serializers.ModelSerializer):
    """Lightweight list row for the backoffice list — no body."""

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ["id", "title", "slug", "status", "author_name", "published_at", "updated_at"]

    def get_author_name(self, obj: BlogPost) -> str:
        return obj.author.get_full_name() or obj.author.username
