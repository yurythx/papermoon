"""
Monta o guia de integração Keycloak e a criação real de client OIDC —
reaproveitado tanto pelas views client-facing (apps.subscriptions.views_client,
o próprio cliente agindo em nome dele mesmo) quanto pelas views staff-facing
(apps.subscriptions.views_admin, o staff do PaperMoon agindo em nome de um
cliente escolhido, pra ajudar com o suporte de uma integração nova).

O guia (`build_integration_guide`) segue só leitura/geração — nunca cria nada
no Keycloak. Os endpoints são calculados pelos paths padrão do protocolo
(sempre corretos pra um Keycloak de verdade) e, quando possível, confirmados
contra o discovery document real (/.well-known/openid-configuration), no
mesmo espírito de apps.accounts.oidc.test_issuer_connectivity — mas sem
bloquear a página se o Keycloak estiver temporariamente inacessível.

`resolve_keycloak_context` é o gate único usado pelo guia, pela criação real e
pela listagem: primeiro confirma que o PaperMoon tem uma conexão central ativa
com ALGUM Keycloak (apps.provisioning.keycloak_config), só depois checa se O
CLIENTE EM QUESTÃO (não necessariamente quem está logado — pode ser o staff
agindo por ele) tem acesso ativo ao serviço "keycloak" — nessa ordem, porque
não faz sentido checar o cliente antes de confirmar que a plataforma consegue
atendê-lo.

`create_client_integration` é a única função que efetivamente cria algo no
Keycloak — levanta exceções tipadas em vez de devolver Response, porque quem
chama (client view vs. admin view) decide como traduzir cada erro pro
chamador: a view do cliente usa uma mensagem genérica (não expõe se o
problema é da plataforma ou da assinatura dele); a view do staff pode e deve
mostrar o motivo exato, já que é staff tentando resolver o problema.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from django.db import IntegrityError
from django.utils.text import slugify
import requests
from rest_framework.exceptions import ValidationError

from apps.audit.utils import log_action
from apps.provisioning.keycloak import (
    KeycloakClientAlreadyExistsError,
    KeycloakConnectionUnavailableError,
    KeycloakProvisioner,
)
from apps.provisioning.keycloak_config import KeycloakConnectionConfig, get_keycloak_connection
from apps.subscriptions.keycloak_integration_content import DEFAULT_SCOPES, LANGUAGE_PACKS
from apps.subscriptions.models import KeycloakClientIntegration, ServiceAccess

logger = logging.getLogger(__name__)


class KeycloakNoServiceAccessError(Exception):
    """O cliente em questão não tem um ServiceAccess 'keycloak' ativo."""


_HTTP_TIMEOUT = 5  # segundos — mesmo valor usado em oidc.py::test_issuer_connectivity

# Literal histórico do guia read-only, de antes de existir criação real de
# client — mantido como fallback quando não há client_secret de verdade pra
# embutir (guia sem client criado ainda), pra não quebrar quem já usa a página
# só pra copiar o formato do código.
_SECRET_PLACEHOLDER_FALLBACK = "COLE_AQUI_O_CLIENT_SECRET"


@dataclass(frozen=True)
class KeycloakContext:
    """Contexto resolvido: conexão central ativa + acesso do cliente ao
    serviço Keycloak, já com o realm/issuer calculados."""

    connection: KeycloakConnectionConfig
    service_access: ServiceAccess
    realm: str
    issuer: str


def resolve_keycloak_context(customer) -> tuple[KeycloakContext | None, str | None]:
    """(contexto, None) se disponível, ou (None, motivo) caso contrário.

    Motivos possíveis: "platform_not_configured" (o PaperMoon ainda não tem
    uma conexão central ativa com nenhum Keycloak) ou "no_service_access" (a
    conexão central existe, mas este cliente não tem um realm provisionado).
    A view decide o que expor pro cliente final a partir daqui — ver
    apps.subscriptions.views_client.
    """
    connection = get_keycloak_connection()
    if not connection.is_usable:
        return None, "platform_not_configured"

    service_access = (
        ServiceAccess.objects.filter(
            license__customer=customer,
            service_key="keycloak",
            status=ServiceAccess.Status.ACTIVE,
        )
        .select_related("license")
        .first()
    )
    if service_access is None or not service_access.external_id:
        return None, "no_service_access"

    realm = service_access.external_id
    issuer = f"{connection.api_url}/realms/{realm}"
    return (
        KeycloakContext(
            connection=connection,
            service_access=service_access,
            realm=realm,
            issuer=issuer,
        ),
        None,
    )


def keycloak_integrations_queryset(customer):
    """Isolamento de tenant: só integrações de ServiceAccess 'keycloak' que
    pertencem a uma license deste customer — mesmo raciocínio de
    DjangoLicenseRepository.get_for_customer. Compartilhado entre a listagem
    client-facing e a admin-facing (staff vendo/gerenciando por um cliente)."""
    return KeycloakClientIntegration.objects.filter(
        service_access__license__customer=customer,
        service_access__service_key="keycloak",
    )


def serialize_keycloak_integration(integration: KeycloakClientIntegration) -> dict:
    return {
        "id": integration.id,
        "client_id": integration.client_id,
        "realm": integration.realm,
        "app_name": integration.app_name,
        "base_url": integration.base_url,
        "redirect_uri": integration.redirect_uri,
        "language": integration.language,
        "public_client": integration.public_client,
        "created_at": integration.created_at,
    }


def standard_endpoints(issuer: str) -> dict[str, str]:
    """Paths padrão do protocolo OIDC do Keycloak — sempre válidos, mesmo
    sem conseguir confirmar via discovery document."""
    return {
        "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
        "token_endpoint": f"{issuer}/protocol/openid-connect/token",
        "userinfo_endpoint": f"{issuer}/protocol/openid-connect/userinfo",
        "jwks_uri": f"{issuer}/protocol/openid-connect/certs",
        "end_session_endpoint": f"{issuer}/protocol/openid-connect/logout",
    }


def try_discovery(issuer: str) -> tuple[dict[str, str] | None, bool]:
    """Tenta confirmar os endpoints reais via /.well-known/openid-configuration.

    Retorna (endpoints, verified). Nunca levanta exceção — qualquer falha de
    rede/parsing só significa "não confirmado", a página continua funcionando
    com os paths padrão calculados por standard_endpoints().
    """
    try:
        resp = requests.get(f"{issuer}/.well-known/openid-configuration", timeout=_HTTP_TIMEOUT)
        resp.raise_for_status()
        doc = resp.json()
    except requests.RequestException as exc:
        logger.info("Keycloak integration guide: discovery indisponível para %s: %s", issuer, exc)
        return None, False
    except ValueError:
        logger.warning("Keycloak integration guide: discovery de %s não é JSON válido", issuer)
        return None, False

    required = (
        "authorization_endpoint",
        "token_endpoint",
        "userinfo_endpoint",
        "jwks_uri",
        "end_session_endpoint",
    )
    if any(key not in doc for key in required):
        return None, False

    return {key: doc[key] for key in required}, True


def resolve_endpoints(issuer: str) -> tuple[dict[str, str], bool]:
    """try_discovery() com fallback pra standard_endpoints() — o par sempre
    usado junto tanto pelo guia quanto pela criação real de client."""
    endpoints, verified = try_discovery(issuer)
    if endpoints is None:
        endpoints = standard_endpoints(issuer)
    return endpoints, verified


def _scopes_go(scopes: list[str]) -> str:
    return ", ".join(f'"{s}"' for s in scopes)


def _scopes_csharp(scopes: list[str]) -> str:
    return "\n".join(f'    options.Scope.Add("{s}");' for s in scopes)


def render_code_snippet(
    *,
    language: str,
    issuer: str,
    client_id: str,
    redirect_uri: str,
    redirect_path: str,
    base_url: str,
    endpoints: dict[str, str],
    client_secret: str | None,
    scopes: list[str] | None = None,
) -> str:
    """Substitui os placeholders `__ALGO__` do code_template do pacote —
    reaproveitado tanto pelo guia read-only (client_secret=None → cai no
    literal placeholder histórico) quanto pela criação real de client
    (client_secret= o valor de verdade devolvido pelo Keycloak)."""
    scopes = scopes if scopes is not None else DEFAULT_SCOPES
    pack = LANGUAGE_PACKS[language]
    context = {
        "__ISSUER__": issuer,
        "__CLIENT_ID__": client_id,
        "__CLIENT_SECRET__": client_secret or _SECRET_PLACEHOLDER_FALLBACK,
        "__REDIRECT_URI__": redirect_uri,
        "__REDIRECT_PATH__": redirect_path,
        "__BASE_URL__": base_url.rstrip("/"),
        "__AUTH_ENDPOINT__": endpoints["authorization_endpoint"],
        "__TOKEN_ENDPOINT__": endpoints["token_endpoint"],
        "__USERINFO_ENDPOINT__": endpoints["userinfo_endpoint"],
        "__JWKS_URI__": endpoints["jwks_uri"],
        "__LOGOUT_ENDPOINT__": endpoints["end_session_endpoint"],
        "__SCOPES_SPACE__": " ".join(scopes),
        "__SCOPES_GO__": _scopes_go(scopes),
        "__SCOPES_CSHARP__": _scopes_csharp(scopes),
    }
    snippet = pack["code_template"]
    for placeholder, value in context.items():
        snippet = snippet.replace(placeholder, value)
    return snippet


def build_integration_guide(
    customer,
    *,
    language: str,
    app_name: str,
    base_url: str,
    redirect_path: str | None,
) -> dict:
    """Monta o dict de resposta pra ClientKeycloakIntegrationGuideView.

    `language` já deve ter sido validado contra LANGUAGE_PACKS pela view
    (KeyError aqui indicaria um bug de validação, não input do usuário).
    """
    ctx, reason = resolve_keycloak_context(customer)
    if ctx is None:
        return {"available": False, "reason": reason}

    pack = LANGUAGE_PACKS[language]
    resolved_redirect_path = redirect_path or pack.get("default_redirect_path", "/auth/callback")
    redirect_uri = base_url.rstrip("/") + resolved_redirect_path
    client_id = slugify(app_name) or "minha-aplicacao"
    scopes = DEFAULT_SCOPES

    endpoints, verified = resolve_endpoints(ctx.issuer)

    code_snippet = render_code_snippet(
        language=language,
        issuer=ctx.issuer,
        client_id=client_id,
        redirect_uri=redirect_uri,
        redirect_path=resolved_redirect_path,
        base_url=base_url,
        endpoints=endpoints,
        client_secret=None,
        scopes=scopes,
    )

    return {
        "available": True,
        "verified": verified,
        "issuer": ctx.issuer,
        "authorization_endpoint": endpoints["authorization_endpoint"],
        "token_endpoint": endpoints["token_endpoint"],
        "userinfo_endpoint": endpoints["userinfo_endpoint"],
        "jwks_uri": endpoints["jwks_uri"],
        "end_session_endpoint": endpoints["end_session_endpoint"],
        "client_id_suggestion": client_id,
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        "language": language,
        "package": pack["package"],
        "install_command": pack["install_command"],
        "steps": pack["steps"],
        "code_snippet": code_snippet,
    }


def validate_language_and_base_url(language: str, base_url: str) -> tuple[str, str]:
    """Validação compartilhada entre GET (guia/lista) e POST (criação),
    client-facing e admin-facing. Levanta DRF ValidationError (400) —
    consistente com o resto da API. Retorna (language, base_url sem barra final)."""
    if language not in LANGUAGE_PACKS:
        raise ValidationError({"language": f"Deve ser um de: {', '.join(LANGUAGE_PACKS)}"})
    if not base_url.startswith(("http://", "https://")):
        raise ValidationError({"base_url": "Informe uma URL http(s) completa."})
    return language, base_url.rstrip("/")


def create_client_integration(
    *,
    customer,
    language: str,
    app_name: str,
    base_url: str,
    redirect_path: str | None,
    actor,
    request=None,
) -> dict:
    """Cria um client OIDC DE VERDADE no realm do `customer` via Admin REST
    API do Keycloak e registra localmente (KeycloakClientIntegration).

    `language`/`base_url` já devem ter sido validados por
    `validate_language_and_base_url` — chamar direto aqui com valores
    inválidos é bug de quem chama (KeyError em LANGUAGE_PACKS), não input do
    usuário. `actor` é quem fica registrado como `created_by`/autor do
    AuditLog — o cliente dele mesmo, ou um membro do staff agindo por ele.

    Levanta (nunca devolve erro serializado — quem chama traduz pra Response):
      KeycloakConnectionUnavailableError  conexão central não configurada/ativa
      KeycloakNoServiceAccessError        `customer` sem ServiceAccess 'keycloak' ativo
      KeycloakClientAlreadyExistsError    client_id já existe (local ou no Keycloak)
      requests.RequestException           Keycloak inacessível/erro de rede
    """
    ctx, reason = resolve_keycloak_context(customer)
    if ctx is None:
        if reason == "platform_not_configured":
            raise KeycloakConnectionUnavailableError()
        raise KeycloakNoServiceAccessError()

    pack = LANGUAGE_PACKS[language]
    public_client = pack["public_client"]
    resolved_redirect_path = redirect_path or pack.get("default_redirect_path", "/auth/callback")
    redirect_uri = base_url + resolved_redirect_path
    client_id = slugify(app_name) or "minha-aplicacao"

    if KeycloakClientIntegration.objects.filter(
        service_access=ctx.service_access, client_id=client_id
    ).exists():
        raise KeycloakClientAlreadyExistsError(client_id)

    provisioner = KeycloakProvisioner()
    result = provisioner.create_oidc_client(
        realm=ctx.realm,
        client_id=client_id,
        name=app_name,
        redirect_uris=[redirect_uri],
        web_origins=[base_url],
        public_client=public_client,
        base_url=base_url,
    )

    try:
        integration = KeycloakClientIntegration.objects.create(
            service_access=ctx.service_access,
            client_id=result["client_id"],
            kc_uuid=result["kc_uuid"],
            realm=ctx.realm,
            app_name=app_name,
            base_url=base_url,
            redirect_uri=redirect_uri,
            language=language,
            public_client=public_client,
            created_by=actor,
        )
    except IntegrityError as exc:
        # Corrida rara: o client já foi criado no Keycloak (acima) mas a linha
        # local colidiu — o client fica órfão no Keycloak (sem tracking local);
        # aceitável para este escopo, não crítico.
        raise KeycloakClientAlreadyExistsError(client_id) from exc

    log_action(
        "keycloak_client_integration.created",
        "KeycloakClientIntegration",
        str(integration.pk),
        user=actor,
        request=request,
        changes={
            "client_id": integration.client_id,
            "realm": integration.realm,
            "language": integration.language,
            "public_client": integration.public_client,
            "customer_id": str(customer.id),
        },
    )

    endpoints, verified = resolve_endpoints(ctx.issuer)
    code_snippet = render_code_snippet(
        language=language,
        issuer=ctx.issuer,
        client_id=integration.client_id,
        redirect_uri=redirect_uri,
        redirect_path=resolved_redirect_path,
        base_url=base_url,
        endpoints=endpoints,
        client_secret=result["client_secret"],
        scopes=DEFAULT_SCOPES,
    )

    return {
        "id": integration.id,
        "client_id": integration.client_id,
        "client_secret": result["client_secret"],
        "public_client": public_client,
        "verified": verified,
        "issuer": ctx.issuer,
        "authorization_endpoint": endpoints["authorization_endpoint"],
        "token_endpoint": endpoints["token_endpoint"],
        "userinfo_endpoint": endpoints["userinfo_endpoint"],
        "jwks_uri": endpoints["jwks_uri"],
        "end_session_endpoint": endpoints["end_session_endpoint"],
        "redirect_uri": redirect_uri,
        "scopes": DEFAULT_SCOPES,
        "language": language,
        "package": pack["package"],
        "install_command": pack["install_command"],
        "steps": pack["steps"],
        "code_snippet": code_snippet,
    }
