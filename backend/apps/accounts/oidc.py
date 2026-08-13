"""
Cliente OIDC fino para SSO de staff via Keycloak.

Ver docs/backend/sso-keycloak-integration.md para o racional completo. Resumo: Keycloak
só emite o `id_token`; quem emite a sessão da PaperMoon continua sendo o Simple JWT
de sempre (ver views.SSOCallbackView). Este módulo cuida só da parte OIDC: gerar a
URL de autorização com PKCE/state/nonce e trocar o `code` pelas claims validadas.

A configuração (issuer/client_id/client_secret/enabled) é editável em runtime pelo
backoffice — ver apps.accounts.sso_config — não vem mais de variáveis de ambiente.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import logging
import secrets
from urllib.parse import urlencode

from django.core.cache import cache
import jwt
from jwt import PyJWKClient
import requests

from apps.accounts.sso_config import SSOConfig, get_sso_config

logger = logging.getLogger(__name__)

_STATE_CACHE_PREFIX = "sso_state:"
_STATE_TTL = 300  # 5 minutos — janela de vida do fluxo de login inteiro
_HTTP_TIMEOUT = 10  # segundos — nunca bloquear a thread do request indefinidamente

# Um PyJWKClient por issuer (não só um global) porque o issuer pode mudar em runtime
# agora que a config vem do banco — troca de issuer não deve reusar chaves cacheadas
# do issuer anterior.
_jwks_clients: dict[str, PyJWKClient] = {}


class SSONotConfiguredError(Exception):
    """SSO desativado ou configuração incompleta (ver backoffice → Configurações)."""


class SSOStateInvalidError(Exception):
    """`state` ausente, expirado ou já consumido."""


class SSOExchangeFailedError(Exception):
    """Falha na troca do código ou na validação do id_token."""


@dataclass(frozen=True)
class SSOClaims:
    email: str
    subject: str
    groups: tuple[str, ...] = ()
    first_name: str = ""
    last_name: str = ""


def _normalize_group(name: str) -> str:
    # O mapper de grupo do Keycloak pode emitir path completo ("/papermoon-staff")
    # ou só o nome ("papermoon-staff") dependendo de como foi configurado —
    # normaliza os dois lados da comparação pra não depender de qual dos dois.
    # Também colapsa espaços internos duplicados: nomes de grupo sincronizados de AD
    # real já apareceram com espaço duplo (ex: "Grupo TI  - HelpDesk") — visualmente
    # idêntico ao configurado no backoffice, mas byte-a-byte diferente sem isso.
    return " ".join(name.strip().lstrip("/").lower().split())


def group_authorizes_staff(configured_group: str, token_groups: tuple[str, ...]) -> bool:
    """True se algum grupo de `configured_group` (SSOConfiguration.staff_group,
    lista separada por vírgula — várias equipes/grupos do AD podem autorizar staff,
    ex: TI + administradores de domínio) aparecer nas claims `groups` do id_token —
    usado pra JIT provisioning (ver SSOCallbackView)."""
    targets = {_normalize_group(g) for g in configured_group.split(",") if g.strip()}
    if not targets:
        return False
    normalized_token_groups = {_normalize_group(g) for g in token_groups}
    return not targets.isdisjoint(normalized_token_groups)


def _require_config() -> SSOConfig:
    config = get_sso_config()
    if not (config.enabled and config.issuer and config.client_id and config.client_secret):
        raise SSONotConfiguredError("SSO desativado ou configuração incompleta.")
    return config


def _get_jwks_client(issuer: str) -> PyJWKClient:
    # PyJWKClient já cacheia as chaves em memória (lifespan=300s) para não bater no
    # /certs do Keycloak a cada login.
    client = _jwks_clients.get(issuer)
    if client is None:
        client = PyJWKClient(
            f"{issuer}/protocol/openid-connect/certs", cache_keys=True, lifespan=300
        )
        _jwks_clients[issuer] = client
    return client


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_authorize_url() -> str:
    """Gera state/nonce/PKCE, persiste no cache e retorna a authorize URL do Keycloak."""
    config = _require_config()

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    code_verifier, code_challenge = _pkce_pair()

    cache.set(
        f"{_STATE_CACHE_PREFIX}{state}",
        {"code_verifier": code_verifier, "nonce": nonce, "issuer": config.issuer},
        timeout=_STATE_TTL,
    )

    params = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        # "groups" só tem efeito se existir um client scope com esse nome no realm
        # (comum quando o mapper de grupo foi anexado a um client scope dedicado,
        # em vez de direto no client) — pedir um scope que não existe no realm é
        # ignorado pelo Keycloak, não quebra o fluxo.
        "scope": "openid email profile groups",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{config.issuer}/protocol/openid-connect/auth?{urlencode(params)}"


def exchange_code(code: str, state: str) -> SSOClaims:
    """Troca o código de autorização pelas claims do id_token, já validadas.

    Levanta SSOStateInvalidError se `state` for desconhecido/expirado/reutilizado, e
    SSOExchangeFailedError para qualquer falha na troca ou validação das claims.
    """
    config = _require_config()

    cache_key = f"{_STATE_CACHE_PREFIX}{state}"
    stored = cache.get(cache_key)
    if not stored:
        raise SSOStateInvalidError("state desconhecido, expirado ou já utilizado.")
    cache.delete(cache_key)  # uso único — um state reaproveitado deve sempre falhar

    # O state guarda o issuer usado no momento do /login — se o admin trocar a config
    # entre o /login e o /callback, o fluxo em andamento termina com o issuer original,
    # não com o que estiver salvo agora (evita misturar credenciais no meio do fluxo).
    issuer = stored.get("issuer") or config.issuer

    try:
        response = requests.post(
            f"{issuer}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.redirect_uri,
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "code_verifier": stored["code_verifier"],
            },
            timeout=_HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("SSO: troca de código com o Keycloak falhou: %s", exc)
        raise SSOExchangeFailedError("Troca de token com o Keycloak falhou.") from exc

    id_token = response.json().get("id_token")
    if not id_token:
        raise SSOExchangeFailedError("Resposta do Keycloak não incluiu id_token.")

    try:
        signing_key = _get_jwks_client(issuer).get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=config.client_id,
            issuer=issuer,
            options={"require": ["exp", "iat", "aud", "iss", "sub"]},
        )
    except jwt.PyJWTError as exc:
        logger.warning("SSO: id_token reprovado na validação: %s", exc)
        raise SSOExchangeFailedError(
            "id_token falhou na validação de assinatura/issuer/audience."
        ) from exc

    if claims.get("nonce") != stored["nonce"]:
        raise SSOExchangeFailedError("nonce do id_token não confere com o da requisição original.")

    email = claims.get("email")
    if not email:
        # Muitas contas do AD (contas de serviço, e também a maioria dos
        # servidores de ponta — saúde, educação — confirmado: 91% dos
        # ~7.600 usuários do realm rondonopolis não têm "mail" preenchido
        # no AD) não têm e-mail cadastrado. Sem isso, o SSO nunca autentica
        # essas contas. Sintetiza um e-mail previsível a partir do username
        # (mesmo padrão observado nas contas que JÁ têm mail: usuario em
        # minúsculas @rondonopolis.mt.gov.br) só para servir de chave de
        # identificação/JIT no papermoon — não é um endereço que recebe
        # e-mail de verdade.
        username = claims.get("preferred_username")
        if username:
            email = f"{username.lower()}@rondonopolis.mt.gov.br"
        else:
            raise SSOExchangeFailedError("id_token não incluiu a claim 'email'.")

    # Claim opcional — só existe se o realm tiver um mapper de grupo anexado ao
    # client (ou a um client scope solicitado). Ausência é normal e não é erro:
    # só significa que o e-mail precisa já existir como staff (sem JIT).
    raw_groups = claims.get("groups") or []
    groups = tuple(raw_groups) if isinstance(raw_groups, list) else ()

    # given_name/family_name são claims padrão do OIDC, mas nem todo mapper do
    # Keycloak as expõe — muitos realms só mandam "name" (nome completo). Faz o
    # split como fallback pra não deixar first_name/last_name vazios à toa (isso
    # é o que faz o autor de posts do blog aparecer como e-mail/username em vez
    # do nome de verdade).
    first_name = (claims.get("given_name") or "").strip()
    last_name = (claims.get("family_name") or "").strip()
    if not first_name and not last_name:
        full_name = (claims.get("name") or "").strip()
        if full_name:
            parts = full_name.split(maxsplit=1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

    return SSOClaims(
        email=email,
        subject=claims["sub"],
        groups=groups,
        first_name=first_name[:150],
        last_name=last_name[:150],
    )


def test_issuer_connectivity(issuer: str) -> dict[str, bool | str]:
    """
    Confirma que o issuer é alcançável e expõe um documento de discovery OIDC válido.

    NÃO valida client_id/client_secret nem faz um login completo — isso exige um
    browser real percorrendo o Authorization Code flow. Para esse teste ponta a
    ponta, use o botão "Entrar com Keycloak" em /login.
    """
    issuer = issuer.rstrip("/")
    if not issuer.startswith(("http://", "https://")):
        return {
            "reachable": False,
            "message": "Issuer inválido — informe uma URL http(s) completa.",
        }

    try:
        resp = requests.get(f"{issuer}/.well-known/openid-configuration", timeout=5)
        resp.raise_for_status()
        doc = resp.json()
    except requests.RequestException as exc:
        return {"reachable": False, "message": f"Não foi possível conectar ao Keycloak: {exc}"}
    except ValueError:
        return {"reachable": False, "message": "O Keycloak respondeu, mas não com um JSON válido."}

    required = ("authorization_endpoint", "token_endpoint", "jwks_uri", "issuer")
    missing = [key for key in required if key not in doc]
    if missing:
        return {
            "reachable": True,
            "message": f"Documento de discovery incompleto (faltando: {', '.join(missing)}).",
        }

    if doc["issuer"].rstrip("/") != issuer:
        return {
            "reachable": True,
            "message": (
                f"Conectou, mas o issuer retornado ({doc['issuer']}) não bate com o "
                f"configurado ({issuer})."
            ),
        }

    return {
        "reachable": True,
        "message": (
            "Realm encontrado e endpoints OIDC válidos. Isso confirma conectividade — "
            'para testar o login completo, use "Entrar com Keycloak" em /login.'
        ),
    }
