from django.contrib import admin
from django.utils.html import format_html

from apps.cms.models import (
    ServiceFAQ,
    ServiceFeatureGroup,
    ServiceFeatureItem,
    ServiceImage,
    ServicePage,
    ServiceResponsibility,
    ServiceStep,
)


class ServiceResponsibilityInline(admin.TabularInline):
    model = ServiceResponsibility
    extra = 1
    fields = ["side", "text", "order"]
    ordering = ["side", "order"]


class ServiceStepInline(admin.TabularInline):
    model = ServiceStep
    extra = 1
    fields = ["number", "title", "description", "order"]
    ordering = ["order"]


class ServiceFeatureItemInline(admin.TabularInline):
    model = ServiceFeatureItem
    extra = 1
    fields = ["text", "order"]
    ordering = ["order"]


class ServiceFeatureGroupInline(admin.TabularInline):
    model = ServiceFeatureGroup
    extra = 1
    fields = ["title", "order"]
    ordering = ["order"]
    show_change_link = True


class ServiceFAQInline(admin.TabularInline):
    model = ServiceFAQ
    extra = 1
    fields = ["question", "answer", "order"]
    ordering = ["order"]


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ["file", "preview", "alt", "caption", "order"]
    readonly_fields = ["preview"]
    ordering = ["order"]

    def preview(self, obj: ServiceImage) -> str:
        if obj.file:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:4px;object-fit:cover;" />',
                obj.file.url,
            )
        return "—"

    preview.short_description = "Preview"  # type: ignore[attr-defined]


@admin.register(ServicePage)
class ServicePageAdmin(admin.ModelAdmin):
    list_display = ["product", "tagline_short", "has_hero", "image_count", "updated_at"]
    list_select_related = ["product"]
    search_fields = ["product__name", "product__slug", "tagline"]
    readonly_fields = ["updated_at", "hero_preview"]
    fieldsets = [
        (
            "Produto",
            {"fields": ["product"]},
        ),
        (
            "Imagem Hero (topo da página)",
            {
                "fields": ["hero_image", "hero_preview", "hero_image_alt"],
                "description": "Substitui o placeholder colorido no canto direito do hero. Convertida para WebP automaticamente.",
            },
        ),
        (
            "Conteúdo principal",
            {"fields": ["tagline", "description"]},
        ),
        (
            "SEO",
            {"fields": ["meta_title", "meta_description"], "classes": ["collapse"]},
        ),
        (
            "Metadados",
            {"fields": ["updated_at"], "classes": ["collapse"]},
        ),
    ]
    inlines = [
        ServiceResponsibilityInline,
        ServiceStepInline,
        ServiceFeatureGroupInline,
        ServiceFAQInline,
        ServiceImageInline,
    ]

    def tagline_short(self, obj: ServicePage) -> str:
        return obj.tagline[:60] or "—"

    tagline_short.short_description = "Tagline"  # type: ignore[attr-defined]

    def has_hero(self, obj: ServicePage) -> bool:
        return bool(obj.hero_image)

    has_hero.boolean = True  # type: ignore[attr-defined]
    has_hero.short_description = "Hero"  # type: ignore[attr-defined]

    def image_count(self, obj: ServicePage) -> int:
        return obj.images.count()

    image_count.short_description = "Imagens"  # type: ignore[attr-defined]

    def hero_preview(self, obj: ServicePage) -> str:
        if obj.hero_image:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:8px;object-fit:contain;" />',
                obj.hero_image.url,
            )
        return "Nenhuma imagem hero cadastrada."

    hero_preview.short_description = "Preview Hero"  # type: ignore[attr-defined]


@admin.register(ServiceFeatureGroup)
class ServiceFeatureGroupAdmin(admin.ModelAdmin):
    """Separate admin to allow editing items inside groups."""

    list_display = ["title", "page", "order"]
    list_select_related = ["page__product"]
    inlines = [ServiceFeatureItemInline]
