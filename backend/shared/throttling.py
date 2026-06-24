from rest_framework.throttling import ScopedRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    """5 tentativas de login por minuto por IP."""

    scope = "login"


class RefreshRateThrottle(ScopedRateThrottle):
    """20 renovações de token por minuto — evita abuso sem prejudicar SPAs."""

    scope = "token_refresh"


class AdminWriteThrottle(ScopedRateThrottle):
    """
    Limita operações destrutivas de admin (criar, suspender, cancelar).
    100 writes/hora é mais que suficiente para uso humano; bloqueia scripts.
    """

    scope = "admin_write"


class PasswordResetRateThrottle(ScopedRateThrottle):
    """
    5 tentativas por hora por IP — previne bomba de e-mail e força-bruta
    de tokens de reset. O endpoint sempre retorna 200, mas o envio de
    e-mail é caro; limitar o ritmo é suficiente.
    """

    scope = "password_reset"


class RegisterRateThrottle(ScopedRateThrottle):
    """5 cadastros por hora por IP — impede criação em massa de contas."""

    scope = "register"
