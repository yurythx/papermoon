from uuid import UUID

from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.licensing.models import ApiKey


class CreateApiKeyCommand:
    def execute(self, customer) -> ApiKey:
        return ApiKey.objects.create(customer=customer)


class RevokeApiKeyCommand:
    def execute(self, pk: UUID | str, customer_id: UUID) -> ApiKey:
        try:
            api_key = ApiKey.objects.get(pk=pk, customer_id=customer_id)
        except ApiKey.DoesNotExist as exc:
            raise NotFound("API Key não encontrada.") from exc

        api_key.is_active = False
        api_key.revoked_at = timezone.now()
        api_key.save()
        cache.delete(f"apikey:{api_key.key}")
        return api_key
