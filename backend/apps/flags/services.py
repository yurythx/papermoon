from __future__ import annotations

from uuid import UUID

from apps.flags.models import FeatureFlag


def list_enabled_keys(customer_id: UUID | None) -> list[str]:
    """Todas as chaves de flag ligadas pra esse customer agora — globais +
    as que esse customer específico foi incluído. Usado por MeView pra
    devolver o conjunto resolvido de uma vez, sem o frontend precisar
    checar flag por flag."""
    global_keys = list(
        FeatureFlag.objects.filter(enabled_globally=True).values_list("key", flat=True)
    )
    if customer_id is None:
        return global_keys
    customer_keys = list(
        FeatureFlag.objects.filter(enabled_customers__id=customer_id)
        .exclude(enabled_globally=True)
        .values_list("key", flat=True)
    )
    return global_keys + customer_keys


def is_enabled(key: str, customer_id: UUID | None) -> bool:
    """Checa uma flag específica — pra lógica de negócio no backend gatear
    algo (ex: dentro de uma task Celery), não só pro frontend decidir o que
    renderizar. Fail-closed: chave inexistente ou sem customer (staff sem
    CustomerProfile) sempre False."""
    try:
        flag = FeatureFlag.objects.get(key=key)
    except FeatureFlag.DoesNotExist:
        return False
    if flag.enabled_globally:
        return True
    if customer_id is None:
        return False
    return flag.enabled_customers.filter(pk=customer_id).exists()
