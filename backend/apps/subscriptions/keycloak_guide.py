"""
Monta o guia de integração Keycloak client-facing (ver
apps.subscriptions.views_client.ClientKeycloakIntegrationGuideView).

Só leitura/geração — nunca cria nada no Keycloak. Os endpoints são
calculados pelos paths padrão do protocolo (sempre corretos pra um Keycloak
de verdade) e, quando possível, confirmados contra o discovery document real
(/.well-known/openid-configuration), no mesmo espírito de
apps.accounts.oidc.test_issuer_connectivity — mas sem bloquear a página se o
Keycloak estiver temporariamente inacessível.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.utils.text import slugify
import requests

from apps.subscriptions.keycloak_integration_content import DEFAULT_SCOPES, LANGUAGE_PACKS
from apps.subscriptions.models import ServiceAccess

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 5  # segundos — mesmo valor usado em oidc.py::test_issuer_connectivity


def _standard_endpoints(issuer: str) -> dict[str, str]:
    """Paths padrão do protocolo OIDC do Keycloak — sempre válidos, mesmo
    sem conseguir confirmar via discovery document."""
    return {
        "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
        "token_endpoint": f"{issuer}/protocol/openid-connect/token",
        "userinfo_endpoint": f"{issuer}/protocol/openid-connect/userinfo",
        "jwks_uri": f"{issuer}/protocol/openid-connect/certs",
        "end_session_endpoint": f"{issuer}/protocol/openid-connect/logout",
    }


def _try_discovery(issuer: str) -> tuple[dict[str, str] | None, bool]:
    """Tenta confirmar os endpoints reais via /.well-known/openid-configuration.

    Retorna (endpoints, verified). Nunca levanta exceção — qualquer falha de
    rede/parsing só significa "não confirmado", a página continua funcionando
    com os paths padrão calculados por _standard_endpoints().
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


def _scopes_go(scopes: list[str]) -> str:
    return ", ".join(f'"{s}"' for s in scopes)


def _scopes_csharp(scopes: list[str]) -> str:
    return "\n".join(f'    options.Scope.Add("{s}");' for s in scopes)


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
        return {"available": False}

    keycloak_api_url = (settings.KEYCLOAK_API_URL or "").rstrip("/")
    if not keycloak_api_url:
        # Provisionador ainda em modo stub neste ambiente (ver core/settings/base.py)
        # — não há Keycloak central real de onde montar o issuer.
        return {"available": False}

    issuer = f"{keycloak_api_url}/realms/{service_access.external_id}"

    pack = LANGUAGE_PACKS[language]
    resolved_redirect_path = redirect_path or pack.get("default_redirect_path", "/auth/callback")
    redirect_uri = base_url.rstrip("/") + resolved_redirect_path
    client_id = slugify(app_name) or "minha-aplicacao"
    scopes = DEFAULT_SCOPES

    endpoints, verified = _try_discovery(issuer)
    if endpoints is None:
        endpoints = _standard_endpoints(issuer)

    context = {
        "__ISSUER__": issuer,
        "__CLIENT_ID__": client_id,
        "__REDIRECT_URI__": redirect_uri,
        "__REDIRECT_PATH__": resolved_redirect_path,
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
    code_snippet = pack["code_template"]
    for placeholder, value in context.items():
        code_snippet = code_snippet.replace(placeholder, value)

    return {
        "available": True,
        "verified": verified,
        "issuer": issuer,
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
