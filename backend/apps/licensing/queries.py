from uuid import UUID

from django.db.models import QuerySet

from apps.licensing.models import ApiKey


def list_api_keys(customer_id: UUID) -> QuerySet:
    """All API keys for a customer, returned as a values queryset for direct serialization."""
    return ApiKey.objects.filter(customer_id=customer_id).values(
        "id", "key", "is_active", "created_at", "revoked_at"
    )
