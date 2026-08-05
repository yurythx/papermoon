from __future__ import annotations

from apps.cms.interfaces import AbstractCMSRepository
from apps.cms.models import ServicePage


class DjangoCMSRepository(AbstractCMSRepository):
    def get_page_by_slug(self, slug: str) -> ServicePage | None:
        # product__is_active=True: um serviço desativado não deve ser
        # alcançável por essa rota pública de jeito nenhum, nem por chamada
        # direta à API — a UI (Next.js) também filtra antes de renderizar,
        # mas a origem da verdade é aqui.
        return (
            ServicePage.objects.select_related("product")
            .prefetch_related(
                "responsibilities",
                "steps",
                "feature_groups__items",
                "faqs",
                "images",
            )
            .filter(product__slug=slug, product__is_active=True)
            .first()
        )

    def list_slugs(self) -> list[str]:
        return list(
            ServicePage.objects.select_related("product")
            .filter(product__is_active=True)
            .values_list("product__slug", flat=True)
        )
