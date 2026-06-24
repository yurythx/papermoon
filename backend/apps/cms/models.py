from __future__ import annotations

import os
from uuid import uuid4

from django.db import models


def _hero_upload_path(instance: ServicePage, filename: str) -> str:
    ext = os.path.splitext(filename)[1] or ".webp"
    return f"cms/heroes/{instance.product.slug}{ext}"


def _gallery_upload_path(instance: ServiceImage, filename: str) -> str:
    ext = os.path.splitext(filename)[1] or ".webp"
    return f"cms/gallery/{instance.page.product.slug}/{uuid4().hex[:8]}{ext}"


class ServicePage(models.Model):
    """One editable page per service/product slug."""

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="cms_page",
        verbose_name="Produto / Serviço",
    )
    hero_image = models.ImageField(
        upload_to=_hero_upload_path,
        null=True,
        blank=True,
        verbose_name="Imagem hero (topo direito)",
        help_text="Substituirá o placeholder colorido. Convertida para WebP automaticamente.",
    )
    hero_image_alt = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Alt text da imagem hero",
    )
    tagline = models.CharField(max_length=200, blank=True, verbose_name="Tagline")
    description = models.TextField(blank=True, verbose_name="Descrição")
    meta_title = models.CharField(max_length=120, blank=True, verbose_name="Meta title (SEO)")
    meta_description = models.TextField(
        max_length=300, blank=True, verbose_name="Meta description (SEO)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cms_service_pages"
        verbose_name = "Página de Serviço"
        verbose_name_plural = "Páginas de Serviço"

    def __str__(self) -> str:
        return f"Página: {self.product.name}"


class ServiceResponsibility(models.Model):
    """Bullet point in the 'O que a PaperMoon faz / o que o cliente faz' section."""

    class Side(models.TextChoices):
        PAPERMOON = "papermoon", "O que a PaperMoon entrega"
        CLIENT = "client", "O que o cliente faz"

    page = models.ForeignKey(
        ServicePage,
        on_delete=models.CASCADE,
        related_name="responsibilities",
    )
    side = models.CharField(max_length=10, choices=Side.choices, verbose_name="Coluna")
    text = models.CharField(max_length=300, verbose_name="Texto do item")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        db_table = "cms_service_responsibilities"
        ordering = ["side", "order"]
        verbose_name = "Responsabilidade"
        verbose_name_plural = "Responsabilidades (PaperMoon / Cliente)"

    def __str__(self) -> str:
        return f"[{self.side}] {self.text[:60]}"


class ServiceStep(models.Model):
    """Numbered implementation step."""

    page = models.ForeignKey(
        ServicePage,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    number = models.CharField(max_length=2, verbose_name='Número (ex: "01")')
    title = models.CharField(max_length=100, verbose_name="Título do passo")
    description = models.TextField(verbose_name="Descrição")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        db_table = "cms_service_steps"
        ordering = ["order"]
        verbose_name = "Passo de implantação"
        verbose_name_plural = "Passos de implantação"

    def __str__(self) -> str:
        return f"{self.number}. {self.title}"


class ServiceFeatureGroup(models.Model):
    """Group of feature bullet points (e.g. 'Comunicação', 'Segurança')."""

    page = models.ForeignKey(
        ServicePage,
        on_delete=models.CASCADE,
        related_name="feature_groups",
    )
    title = models.CharField(max_length=100, verbose_name="Título do grupo")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        db_table = "cms_service_feature_groups"
        ordering = ["order"]
        verbose_name = "Grupo de Funcionalidades"
        verbose_name_plural = "Grupos de Funcionalidades"

    def __str__(self) -> str:
        return self.title


class ServiceFeatureItem(models.Model):
    """Single feature bullet point inside a group."""

    group = models.ForeignKey(
        ServiceFeatureGroup,
        on_delete=models.CASCADE,
        related_name="items",
    )
    text = models.CharField(max_length=200, verbose_name="Item")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        db_table = "cms_service_feature_items"
        ordering = ["order"]
        verbose_name = "Item de Funcionalidade"
        verbose_name_plural = "Itens de Funcionalidade"

    def __str__(self) -> str:
        return self.text[:80]


class ServiceFAQ(models.Model):
    """Frequently Asked Question for a service page."""

    page = models.ForeignKey(
        ServicePage,
        on_delete=models.CASCADE,
        related_name="faqs",
    )
    question = models.CharField(max_length=300, verbose_name="Pergunta")
    answer = models.TextField(verbose_name="Resposta")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        db_table = "cms_service_faqs"
        ordering = ["order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self) -> str:
        return self.question[:80]


class ServiceImage(models.Model):
    """Gallery image for a service page. Converted to WebP on save."""

    page = models.ForeignKey(
        ServicePage,
        on_delete=models.CASCADE,
        related_name="images",
    )
    file = models.ImageField(
        upload_to=_gallery_upload_path,
        verbose_name="Imagem",
        help_text="Convertida para WebP automaticamente. Máx 1200px de largura.",
    )
    alt = models.CharField(max_length=200, verbose_name="Alt text", blank=True)
    caption = models.CharField(max_length=300, blank=True, verbose_name="Legenda")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        db_table = "cms_service_images"
        ordering = ["order"]
        verbose_name = "Imagem da galeria"
        verbose_name_plural = "Imagens da galeria"

    def __str__(self) -> str:
        return f"Imagem {self.order} — {self.page}"
