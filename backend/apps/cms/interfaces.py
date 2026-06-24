from __future__ import annotations

from abc import ABC, abstractmethod

from apps.cms.models import ServicePage


class AbstractCMSRepository(ABC):
    @abstractmethod
    def get_page_by_slug(self, slug: str) -> ServicePage | None: ...

    @abstractmethod
    def list_slugs(self) -> list[str]: ...
