from __future__ import annotations

from django.utils.text import slugify
from rest_framework import serializers

from apps.blog.models import BlogPost, Tag
from shared.public_urls import build_public_media_url

WORDS_PER_MINUTE = (
    200  # mesma aproximação usada em frontend/src/lib/blog.ts — mantenha os dois em sincronia
)


def _estimate_reading_time(body: str) -> int:
    words = len(body.split())
    return max(1, round(words / WORDS_PER_MINUTE))


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "slug"]


def _resolve_tags(names: list[str]) -> list[Tag]:
    """get_or_create por slug (não por nome) — evita duas tags "GLPI"/"glpi"
    coexistindo só por causa de maiúscula, sem impor um vocabulário fixo."""
    tags: list[Tag] = []
    seen_slugs: set[str] = set()
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        slug = slugify(name)[:60]
        if not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name[:50]})
        tags.append(tag)
    return tags


class BlogPostPublicListSerializer(serializers.ModelSerializer):
    """Card row for /blog — no body, keeps the listing payload light."""

    cover_image_url = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    reading_time = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

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
            "reading_time",
            "tags",
        ]

    def get_cover_image_url(self, obj: BlogPost) -> str | None:
        request = self.context.get("request")
        return build_public_media_url(
            obj.cover_image.url if obj.cover_image else None, request=request
        )

    def get_author_name(self, obj: BlogPost) -> str:
        return obj.author.get_full_name() or obj.author.username

    def get_reading_time(self, obj: BlogPost) -> int:
        return _estimate_reading_time(obj.body)


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
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
        help_text="Nomes de tags — cria automaticamente as que não existirem ainda.",
    )

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
            "tags",
            "tag_names",
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

    def create(self, validated_data: dict) -> BlogPost:
        tag_names = validated_data.pop("tag_names", None)
        post = BlogPost.objects.create(**validated_data)
        if tag_names is not None:
            post.tags.set(_resolve_tags(tag_names))
        return post

    def update(self, instance: BlogPost, validated_data: dict) -> BlogPost:
        tag_names = validated_data.pop("tag_names", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.mark_published()
        instance.save()
        if tag_names is not None:
            instance.tags.set(_resolve_tags(tag_names))
        return instance


class BlogPostAdminListSerializer(serializers.ModelSerializer):
    """Lightweight list row for the backoffice list — no body."""

    author_name = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "status",
            "author_name",
            "published_at",
            "updated_at",
            "tags",
        ]

    def get_author_name(self, obj: BlogPost) -> str:
        return obj.author.get_full_name() or obj.author.username
