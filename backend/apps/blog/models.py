from __future__ import annotations

import os
from uuid import uuid4

from django.db import models
from django.utils import timezone


def _blog_cover_upload_path(instance: BlogPost, filename: str) -> str:
    ext = os.path.splitext(filename)[1] or ".webp"
    return f"blog/covers/{instance.slug}{ext}"


class BlogPost(models.Model):
    """A blog post authored by staff — best practices, implementation notes,
    news about the services PaperMoon offers. Public once status=PUBLISHED.

    Deliberately no categories/tags/comments in this first version — see
    docs/backend/blog.md for the rationale (content-ops risk > engineering
    risk; ship the smallest useful thing first)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        PUBLISHED = "published", "Publicado"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    excerpt = models.CharField(
        max_length=300,
        help_text="Resumo curto — usado no card da listagem e como meta description padrão.",
    )
    body = models.TextField(
        blank=True,
        help_text="Corpo do post em Markdown. Vazio ao criar — preenchido no editor completo.",
    )
    cover_image = models.ImageField(
        upload_to=_blog_cover_upload_path,
        null=True,
        blank=True,
        help_text="Convertida para WebP automaticamente.",
    )
    cover_image_alt = models.CharField(max_length=200, blank=True)
    author = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.PROTECT,
        related_name="blog_posts",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    meta_title = models.CharField(max_length=120, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blog_posts"
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["status", "published_at"])]

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    def mark_published(self) -> None:
        """Sets published_at on first publish only — republishing (e.g. a typo
        fix after unpublishing) doesn't reset the original publish date."""
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
