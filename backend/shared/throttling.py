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


class SSORateThrottle(ScopedRateThrottle):
    """20 tentativas/minuto por IP nos endpoints de SSO (login e callback)."""

    scope = "sso"


class SSOTestRateThrottle(ScopedRateThrottle):
    """10 testes de conectividade/minuto — mais folgado que admin_write pois é
    diagnóstico (o admin pode querer testar algumas vezes seguidas ajustando a URL)."""

    scope = "sso_test"


class KeycloakConnectionTestRateThrottle(ScopedRateThrottle):
    """10 testes de conectividade/minuto com o Keycloak central — mesmo raciocínio
    de SSOTestRateThrottle, conexão diferente (provisionamento, não SSO de staff)."""

    scope = "keycloak_connection_test"


class KeycloakClientCreateRateThrottle(ScopedRateThrottle):
    """20 criações de client OIDC/hora por cliente — cria infra de verdade no
    Keycloak, então mais restrito que um GET, mas folgado o bastante pra um
    cliente com várias integrações (uma por linguagem/ambiente) sem travar."""

    scope = "keycloak_client_create"
