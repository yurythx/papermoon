from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from django.db.models import QuerySet

if TYPE_CHECKING:
    from apps.subscriptions.models import License


class AbstractLicenseRepository(ABC):
    """
    Read-only contract for license data access.

    Follows Interface Segregation: only the operations the client-facing
    views actually need. Admin queries go through the ORM or a separate
    admin query module — not through this interface.
    """

    @abstractmethod
    def list_by_customer(self, customer_id: UUID) -> QuerySet:
        """Return all licenses for a customer, newest first."""

    @abstractmethod
    def get_for_customer(self, license_id: UUID, customer_id: UUID) -> License:
        """
        Return a single license that belongs to the given customer.
        Raises NotFound if not found or belongs to a different tenant.
        """
