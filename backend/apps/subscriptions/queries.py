from __future__ import annotations

from uuid import UUID

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound

from apps.subscriptions.models import Subscription

_BASE_SELECT = ("customer", "product", "pricing", "license")
_BASE_PREFETCH = ("license__service_accesses",)


def list_subscriptions_admin(
    *,
    customer_id: str | None = None,
    search: str | None = None,
    status: str | None = None,
    ordering: str = "-created_at",
) -> QuerySet:
    """Admin-side subscription listing with optional filters. CQRS read path."""
    allowed_orderings = {"created_at", "-created_at", "expires_at", "-expires_at"}
    qs = Subscription.objects.select_related(*_BASE_SELECT).prefetch_related(*_BASE_PREFETCH)
    if customer_id:
        qs = qs.filter(customer_id=customer_id)
    if search and search.strip():
        qs = qs.filter(customer__company_name__icontains=search.strip())
    if status:
        qs = qs.filter(status=status)
    return qs.order_by(ordering if ordering in allowed_orderings else "-created_at")


def get_subscription_by_id(subscription_id: str | UUID) -> Subscription:
    try:
        return (
            Subscription.objects.select_related(*_BASE_SELECT)
            .prefetch_related(*_BASE_PREFETCH)
            .get(pk=subscription_id)
        )
    except Subscription.DoesNotExist as exc:
        raise NotFound(f"Assinatura {subscription_id} não encontrada.") from exc


def list_client_subscriptions(customer_id: UUID) -> QuerySet:
    """Client-scoped subscription list — tenant isolation enforced here, not in the view."""
    return (
        Subscription.objects.filter(customer_id=customer_id)
        .select_related(*_BASE_SELECT)
        .prefetch_related(*_BASE_PREFETCH)
        .order_by("-created_at")
    )


def get_client_subscription(pk: str | UUID, customer_id: UUID) -> Subscription:
    """Single subscription scoped to the authenticated customer's tenant."""
    try:
        return (
            Subscription.objects.select_related(*_BASE_SELECT)
            .prefetch_related(*_BASE_PREFETCH)
            .get(pk=pk, customer_id=customer_id)
        )
    except Subscription.DoesNotExist as exc:
        raise NotFound(f"Assinatura {pk} não encontrada.") from exc
