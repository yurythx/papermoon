from uuid import UUID

from django.http import HttpRequest

from apps.audit.models import AuditLog
from shared.net import get_client_ip


def log_action(
    action: str,
    resource_type: str,
    resource_id: str | UUID,
    user=None,
    changes: dict | None = None,
    request: HttpRequest | None = None,
) -> AuditLog:
    # NUM_PROXIES-aware (ver shared/net.py) em vez de confiar cegamente no
    # primeiro valor de X-Forwarded-For — mesmo raciocínio do LoginAttemptGuard.
    # ip_address é GenericIPAddressField — "unknown" (fallback do helper
    # quando não há META nenhum) não é um IP válido, precisa virar None.
    resolved_ip = get_client_ip(request) if request else None
    ip = resolved_ip if resolved_ip and resolved_ip != "unknown" else None

    return AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        changes=changes or {},
        ip_address=ip,
    )
