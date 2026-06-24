from __future__ import annotations

from apps.cms.interfaces import AbstractCMSRepository
from apps.cms.models import ServicePage


class DjangoCMSRepository(AbstractCMSRepository):
    def get_page_by_slug(self, slug: str) -> ServicePage | None:
        return (
            ServicePage.objects.select_related("product")
            .prefetch_related(
                "responsibilities",
                "steps",
                "feature_groups__items",
                "faqs",
                "images",
            )
            .filter(product__slug=slug)
            .first()
        )

    def list_slugs(self) -> list[str]:
        return list(
            ServicePage.objects.select_related("product").values_list("product__slug", flat=True)
        )
