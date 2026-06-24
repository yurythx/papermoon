from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings
import requests

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def revalidate_service_page(self, slug: str) -> None:
    """Notify Next.js to invalidate ISR cache for /servicos/{slug}.

    Called after ServicePage is saved. Fails silently — the page will
    revalidate automatically after `revalidate: 60` seconds regardless.
    """
    nextjs_url = getattr(settings, "NEXTJS_INTERNAL_URL", "")
    secret = getattr(settings, "REVALIDATE_SECRET", "")

    if not nextjs_url or not secret:
        logger.debug("cms.revalidate: NEXTJS_INTERNAL_URL or REVALIDATE_SECRET not set, skipping.")
        return

    try:
        resp = requests.post(
            f"{nextjs_url}/api/revalidate",
            json={"secret": secret, "slug": slug},
            timeout=5,
        )
        resp.raise_for_status()
        logger.info("cms.revalidate: slug=%s status=%s", slug, resp.status_code)
    except Exception as exc:
        logger.warning("cms.revalidate failed slug=%s error=%s", slug, exc)
        try:
            raise self.retry(exc=exc)
        except Exception:
            pass  # Max retries reached — ISR will catch up on next request
