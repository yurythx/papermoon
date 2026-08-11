"""
Conexão central do PaperMoon com o Keycloak que ELE administra via Admin REST
API (provisionamento de realms/clients de clientes), editável em runtime via
backoffice (Configurações).

NÃO confundir com apps.accounts.sso_config — aquilo é o SSO de STAFF (como o
time do PaperMoon entra no próprio backoffice). São Keycloaks diferentes.

Espelha apps/accounts/sso_config.py no padrão (cache Redis curto, secret
criptografado com shared/crypto.py, "vazio mantém o já salvo" no update).
"""

from __future__ import annotations

from dataclasses import dataclass

from django.core.cache import cache
import requests

from apps.accounts.models import CustomUser
from apps.provisioning.models import KeycloakConnection
from shared.crypto import decrypt_secret, encrypt_secret

_CACHE_KEY = "keycloak_connection:active"
_CACHE_TTL = 30  # segundos — curto o bastante pra uma mudança no backoffice refletir quase na hora


@dataclass(frozen=True)
class KeycloakConnectionConfig:
    enabled: bool
    api_url: str
    admin_token: str

    @property
    def is_usable(self) -> bool:
        return bool(self.enabled and self.api_url and self.admin_token)


def get_keycloak_connection() -> KeycloakConnectionConfig:
    cached = cache.get(_CACHE_KEY)
    if cached is not None:
        return cached

    row = KeycloakConnection.get_solo()
    config = KeycloakConnectionConfig(
        enabled=row.enabled,
        api_url=row.api_url,
        admin_token=decrypt_secret(row.admin_token_encrypted),
    )
    cache.set(_CACHE_KEY, config, timeout=_CACHE_TTL)
    return config


def invalidate_keycloak_connection_cache() -> None:
    cache.delete(_CACHE_KEY)


def update_keycloak_connection(
    *,
    enabled: bool,
    api_url: str,
    admin_token: str | None,
    user: CustomUser,
) -> KeycloakConnection:
    """`admin_token=None` (ou "") mantém o token já salvo — só troca quando um
    valor novo é enviado, para o admin não precisar redigitar o token a cada save."""
    row = KeycloakConnection.get_solo()
    row.enabled = enabled
    row.api_url = api_url.rstrip("/")
    if admin_token:
        row.admin_token_encrypted = encrypt_secret(admin_token)
    row.updated_by = user
    row.save()
    invalidate_keycloak_connection_cache()
    return row


def open_admin_session() -> tuple[requests.Session | None, str]:
    """Sessão HTTP pronta pra chamar o Admin REST API do Keycloak central, ou
    (None, "") se a conexão não estiver configurada/ativa — quem chama decide
    como degradar (normalmente: modo stub)."""
    config = get_keycloak_connection()
    if not config.is_usable:
        return None, ""

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {config.admin_token}",
            "Content-Type": "application/json",
        }
    )
    return session, config.api_url


def test_admin_connectivity(api_url: str, admin_token: str) -> dict[str, bool | str]:
    """
    Confirma que o Keycloak é alcançável e que o admin_token é aceito pelo
    Admin REST API. Diferente de apps.accounts.oidc.test_issuer_connectivity
    (que é um GET público no discovery document) — aqui a chamada é
    autenticada, contra um endpoint de administração.
    """
    api_url = api_url.rstrip("/")
    if not api_url.startswith(("http://", "https://")):
        return {
            "reachable": False,
            "message": "URL da API inválida — informe uma URL http(s) completa.",
        }

    try:
        resp = requests.get(
            f"{api_url}/admin/realms",
            params={"briefRepresentation": "true"},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5,
        )
    except requests.RequestException as exc:
        return {"reachable": False, "message": f"Não foi possível conectar ao Keycloak: {exc}"}

    if resp.status_code in (401, 403):
        return {
            "reachable": True,
            "message": "Conectou, mas o admin_token foi recusado (401/403) — verifique o token.",
        }

    if not resp.ok:
        return {
            "reachable": True,
            "message": f"Conectou, mas o Keycloak respondeu com erro (HTTP {resp.status_code}).",
        }

    try:
        realms = resp.json()
        count = len(realms) if isinstance(realms, list) else "?"
    except ValueError:
        return {
            "reachable": True,
            "message": "Conectou e o token foi aceito, mas a resposta não veio em JSON.",
        }

    return {
        "reachable": True,
        "message": f"Conectou e o token foi aceito — {count} realm(s) visível(is).",
    }
