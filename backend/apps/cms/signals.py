"""Convert images to WebP on save; trigger ISR revalidation after save."""

from __future__ import annotations

import logging
import os

from django.core.files.base import ContentFile
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.cms.models import ServiceImage, ServicePage
from apps.cms.services import ImageProcessor

logger = logging.getLogger(__name__)


def _replace_with_webp(field_file, slug_for_path: str, subfolder: str) -> None:
    """Read the pending upload, convert to WebP, replace in-memory before DB write.

    Uploads coming through the API views are already validated (see
    apps.cms.services.validate_image_upload) — this only re-raises for
    other paths that can set these fields (Django Admin, fixtures/scripts),
    so a non-image never gets silently persisted as-is under an image URL.
    """
    if not field_file:
        return
    field_file.seek(0)
    original_bytes = field_file.read()
    try:
        webp_bytes = ImageProcessor.to_webp(original_bytes)
    except Exception:
        logger.exception(
            "Falha ao converter upload para WebP (subfolder=%s, slug=%s) — rejeitando.",
            subfolder,
            slug_for_path,
        )
        raise
    base = os.path.splitext(os.path.basename(field_file.name))[0]
    new_name = f"cms/{subfolder}/{slug_for_path}/{base}.webp"
    field_file.file = ContentFile(webp_bytes)
    field_file.name = new_name


@receiver(pre_save, sender=ServicePage)
def convert_hero_to_webp(
    sender: type[ServicePage], instance: ServicePage, **kwargs: object
) -> None:
    if not instance.hero_image:
        return
    # Only process newly uploaded files, not a page re-saved for unrelated
    # reasons (e.g. editing FAQs re-triggers pre_save for the whole model).
    # hasattr(field_file, "file") is *always* True once accessed — Django's
    # FieldFile.file is a property that lazily opens from storage on demand,
    # for an already-persisted path just as much as a fresh upload (verified
    # against django/db/models/fields/files.py). `_committed` is the actual
    # signal Django itself uses for "this is a pending, not-yet-saved file"
    # (set False in FileDescriptor.__get__ when a raw upload is assigned).
    if not instance.hero_image._committed:
        slug = instance.product.slug if instance.product_id else "unknown"
        _replace_with_webp(instance.hero_image, slug, "heroes")


@receiver(pre_save, sender=ServiceImage)
def convert_gallery_image_to_webp(
    sender: type[ServiceImage], instance: ServiceImage, **kwargs: object
) -> None:
    if not instance.file:
        return
    if not instance.file._committed:  # see convert_hero_to_webp for why
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
