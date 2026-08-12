"""Convert cover images to WebP on save; trigger ISR revalidation after save.

Mirrors apps/cms/signals.py exactly — same anti-pattern to avoid
(hasattr(field_file, "file") is always True; _committed is the real signal
for "this is a pending upload"), same image pipeline. Reuses
apps.cms.services.ImageProcessor directly instead of duplicating it — it's
already a pure bytes-in/bytes-out utility with no Django model coupling
(see its own SRP docstring), so there's nothing CMS-specific to fork.
"""

from __future__ import annotations

import logging
import os

from django.core.files.base import ContentFile
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.blog.models import BlogPost
from apps.cms.services import ImageProcessor

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=BlogPost)
def convert_cover_to_webp(sender: type[BlogPost], instance: BlogPost, **kwargs: object) -> None:
    if not instance.cover_image:
        return
    if instance.cover_image._committed:  # see apps/cms/signals.py for why
        return

    instance.cover_image.seek(0)
    original_bytes = instance.cover_image.read()
    try:
        webp_bytes = ImageProcessor.to_webp(original_bytes)
    except Exception:
        logger.exception(
            "Falha ao converter capa de post para WebP (slug=%s) — rejeitando.", instance.slug
        )
        raise
    base = os.path.splitext(os.path.basename(instance.cover_image.name))[0]
    instance.cover_image.file = ContentFile(webp_bytes)
    instance.cover_image.name = f"blog/covers/{instance.slug}/{base}.webp"


@receiver(post_save, sender=BlogPost)
def trigger_revalidation_on_post_save(
    sender: type[BlogPost], instance: BlogPost, **kwargs: object
) -> None:
    from apps.blog.tasks import revalidate_blog_post

    revalidate_blog_post.delay(instance.slug)


@receiver(post_delete, sender=BlogPost)
def trigger_revalidation_on_post_delete(
    sender: type[BlogPost], instance: BlogPost, **kwargs: object
) -> None:
    # Sem isso, excluir um post publicado não purga o ISR — /blog/<slug>, a
    # listagem e o RSS continuam servindo o conteúdo apagado até a janela
    # passiva de revalidate=60s expirar, mesmo a API do Django já dando 404.
    from apps.blog.tasks import revalidate_blog_post

    revalidate_blog_post.delay(instance.slug)
