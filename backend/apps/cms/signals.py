"""Convert images to WebP on save; trigger ISR revalidation after save."""

from __future__ import annotations

import os

from django.core.files.base import ContentFile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.cms.models import ServiceImage, ServicePage
from apps.cms.services import ImageProcessor


def _replace_with_webp(field_file, slug_for_path: str, subfolder: str) -> None:
    """Read the pending upload, convert to WebP, replace in-memory before DB write."""
    if not field_file or not hasattr(field_file, "file"):
        return
    try:
        field_file.seek(0)
        original_bytes = field_file.read()
        webp_bytes = ImageProcessor.to_webp(original_bytes)
        base = os.path.splitext(os.path.basename(field_file.name))[0]
        new_name = f"cms/{subfolder}/{slug_for_path}/{base}.webp"
        field_file.file = ContentFile(webp_bytes)
        field_file.name = new_name
    except Exception:
        # Never block a save because of image processing — the original is kept.
        pass


@receiver(pre_save, sender=ServicePage)
def convert_hero_to_webp(
    sender: type[ServicePage], instance: ServicePage, **kwargs: object
) -> None:
    if not instance.hero_image:
        return
    # Only process newly uploaded files (not already-saved paths)
    if hasattr(instance.hero_image, "file"):
        slug = instance.product.slug if instance.product_id else "unknown"
        _replace_with_webp(instance.hero_image, slug, "heroes")


@receiver(pre_save, sender=ServiceImage)
def convert_gallery_image_to_webp(
    sender: type[ServiceImage], instance: ServiceImage, **kwargs: object
) -> None:
    if not instance.file:
        return
    if hasattr(instance.file, "file"):
        slug = (
            instance.page.product.slug
            if instance.page_id and instance.page.product_id
            else "unknown"
        )
        _replace_with_webp(instance.file, slug, "gallery")


@receiver(post_save, sender=ServicePage)
def trigger_revalidation_on_page_save(
    sender: type[ServicePage], instance: ServicePage, **kwargs: object
) -> None:
    from apps.cms.tasks import revalidate_service_page

    slug = instance.product.slug if instance.product_id else None
    if slug:
        revalidate_service_page.delay(slug)


@receiver(post_save, sender=ServiceImage)
def trigger_revalidation_on_image_save(
    sender: type[ServiceImage], instance: ServiceImage, **kwargs: object
) -> None:
    from apps.cms.tasks import revalidate_service_page

    try:
        slug = instance.page.product.slug
        revalidate_service_page.delay(slug)
    except Exception:
        pass
