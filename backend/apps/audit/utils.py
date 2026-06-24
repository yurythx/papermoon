from django.http import HttpRequest

from apps.audit.models import AuditLog


def log_action(
    action: str,
    resource_type: str,
    resource_id: str,
    user=None,
    changes: dict | None = None,
    request: HttpRequest | None = None,
) -> AuditLog:
    ip = None
    if request:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.META.get("REMOTE_ADDR")
        )

    return AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        changes=changes or {},
        ip_address=ip,
    )
