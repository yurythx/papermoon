"""
Configuração de SSO de staff, editável em runtime via backoffice (Configurações).

Substitui o desenho anterior (KEYCLOAK_SSO_* em .env) — ver
docs/backend/sso-keycloak-integration.md para o histórico completo dessa mudança.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

from apps.accounts.models import CustomUser, SSOConfiguration
from shared.crypto import decrypt_secret, encrypt_secret

_CACHE_KEY = "sso_config:active"
_CACHE_TTL = 30  # segundos — curto o bastante pra uma mudança no backoffice refletir quase na hora


@dataclass(frozen=True)
class SSOConfig:
    enabled: bool
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str


def _redirect_uri() -> str:
    return f"{settings.FRONTEND_URL}/api/auth/sso/callback"


def get_sso_config() -> SSOConfig:
    cached = cache.get(_CACHE_KEY)
    if cached is not None:
        return cached

    row = SSOConfiguration.get_solo()
    config = SSOConfig(
        enabled=row.enabled,
        issuer=row.issuer,
        client_id=row.client_id,
        client_secret=decrypt_secret(row.client_secret_encrypted),
        redirect_uri=_redirect_uri(),
    )
    cache.set(_CACHE_KEY, config, timeout=_CACHE_TTL)
    return config


def invalidate_sso_config_cache() -> None:
    cache.delete(_CACHE_KEY)


def update_sso_config(
    *,
    enabled: bool,
    issuer: str,
    client_id: str,
    client_secret: str | None,
    user: CustomUser,
) -> SSOConfiguration:
    """`client_secret=None` (ou "") mantém o segredo já salvo — só troca quando um
    valor novo é enviado, para o admin não precisar redigitar o segredo a cada save."""
    row = SSOConfiguration.get_solo()
    row.enabled = enabled
    row.issuer = issuer.rstrip("/")
    row.client_id = client_id
    if client_secret:
        row.client_secret_encrypted = encrypt_secret(client_secret)
    row.updated_by = user
    row.save()
    invalidate_sso_config_cache()
    return row
