from __future__ import annotations

from uuid import UUID

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound

from apps.subscriptions.interfaces import AbstractLicenseRepository
from apps.subscriptions.models import License


class DjangoLicenseRepository(AbstractLicenseRepository):
    """
    ORM implementation of AbstractLicenseRepository.

    select_related pre-fetches subscription → product + pricing in a single
    JOIN so the serializer never issues N+1 queries for product_name or
    billing_cycle. prefetch_related handles the reverse FK to service_accesses
    (a separate query, but batched by Django — not N+1).
    """

    def list_by_customer(self, customer_id: UUID) -> QuerySet:
        return (
            License.objects.select_related(
                "subscription__product",
                "subscription__pricing",
            )
            .prefetch_related("service_accesses")
            .filter(customer_id=customer_id)
            .order_by("-created_at")
        )

    def get_for_customer(self, license_id: UUID, customer_id: UUID) -> License:
        try:
            return (
                License.objects.select_related(
                    "subscription__product",
                    "subscription__pricing",
                )
                .prefetch_related("service_accesses")
                .get(id=license_id, customer_id=customer_id)
            )
        except License.DoesNotExist as exc:
            raise NotFound(f"Licença {license_id} não encontrada.") from exc
