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


class SSOStatusRateThrottle(ScopedRateThrottle):
    """300/minuto por IP — bem mais folgado que o 'anon' padrão (200/dia).

    Motivo: este é um GET público, só-leitura, consultado pelo BFF (Next.js)
    a cada visita à tela de login — e o BFF faz essa chamada server-to-server,
    então TODOS os visitantes do site compartilham o mesmo IP de origem do
    ponto de vista do Django. Com o throttle 'anon' padrão (200/dia), esse
    bucket compartilhado estoura com tráfego normal, devolve 429, e o BFF
    (que falha fechado por design — esconde o botão em vez de quebrar a
    página) esconde "Entrar com Keycloak" pra todo mundo. Bug real observado
    em produção; corrigido dando um scope próprio e generoso a este endpoint."""

    scope = "sso_status"


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


class AsaasWebhookRateThrottle(ScopedRateThrottle):
    """600/minuto por IP — a autenticação real é o header asaas-access-token
    (comparado com hmac.compare_digest, obrigatório em produção), este
    throttle é só uma camada extra contra alguém martelando o endpoint
    tentando adivinhar o token. Bem folgado pra não derrubar rajadas
    legítimas de eventos do Asaas em dias de fechamento de fatura."""

    scope = "asaas_webhook"


class ValidateKeyRateThrottle(ScopedRateThrottle):
    """600/minuto por IP — /validate-key/ é chamado a cada requisição por
    automações externas (n8n, uma instância por customer), não por um único
    servidor interno como ActiveServiceSlugsView, então zerar o throttle
    aqui abriria uma superfície de força-bruta pra adivinhar API Keys
    válidas. 600/min é folgado o bastante pra não atrapalhar uso legítimo
    intenso, mas limita o custo de uma campanha de tentativa e erro."""

    scope = "validate_key"
