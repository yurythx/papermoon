from django.contrib import admin
from django.utils.html import format_html

from apps.blog.models import BlogPost, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "status", "published_at", "updated_at"]
    list_filter = ["status", "tags"]
    search_fields = ["title", "slug", "excerpt", "author__email"]
    readonly_fields = ["id", "created_at", "updated_at", "cover_preview"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["tags"]
    fieldsets = [
        ("Conteúdo", {"fields": ["title", "slug", "excerpt", "body", "author", "tags"]}),
        (
            "Capa",
            {
                "fields": ["cover_image", "cover_preview", "cover_image_alt"],
                "description": "Convertida para WebP automaticamente.",
            },
        ),
        ("Publicação", {"fields": ["status", "published_at"]}),
        ("SEO", {"fields": ["meta_title", "meta_description"], "classes": ["collapse"]}),
        ("Metadados", {"fields": ["id", "created_at", "updated_at"], "classes": ["collapse"]}),
    ]
    actions = ["publish_posts"]

    def cover_preview(self, obj: BlogPost) -> str:
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:8px;object-fit:contain;" />',
                obj.cover_image.url,
            )
        return "Nenhuma capa cadastrada."

    cover_preview.short_description = "Preview"  # type: ignore[attr-defined]

    @admin.action(description="Publicar posts selecionados")
    def publish_posts(self, request, queryset) -> None:
        updated = 0
        for post in queryset.filter(status=BlogPost.Status.DRAFT):
            post.status = BlogPost.Status.PUBLISHED
            post.mark_published()
            post.save()
            updated += 1
        self.message_user(request, f"{updated} post(s) publicado(s).")
