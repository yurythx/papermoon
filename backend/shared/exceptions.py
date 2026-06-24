from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response


class SubscriptionSuspendedError(Exception):
    pass


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    # Lazy import avoids circular dependency: rest_framework.views reads
    # EXCEPTION_HANDLER (this module) during its own initialization.
    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)

    if isinstance(exc, SubscriptionSuspendedError):
        return Response(
            {
                "code": "subscription_suspended",
                "message": "Sua assinatura está suspensa. Entre em contato com o suporte.",
                "details": [],
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if response is None:
        return None

    error_map = {
        AuthenticationFailed: "authentication_failed",
        NotAuthenticated: "authentication_failed",
        PermissionDenied: "permission_denied",
        NotFound: "not_found",
        ValidationError: "validation_error",
    }

    code = next(
        (v for k, v in error_map.items() if isinstance(exc, k)),
        "internal_error",
    )

    detail = response.data
    if isinstance(detail, dict):
        message = str(detail.get("detail", exc))
        details = []
    elif isinstance(detail, list):
        message = str(detail[0]) if detail else str(exc)
        details = [str(d) for d in detail]
    else:
        message = str(detail)
        details = []

    response.data = {
        "code": code,
        "message": message,
        "details": details,
    }
    return response
