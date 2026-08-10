"""
Unit tests for apps/accounts/oidc.py (Keycloak SSO client for staff login).

Network calls (token exchange, JWKS fetch) and JWT signature validation are mocked —
no real Keycloak is needed. Config now lives in SSOConfiguration (DB), not settings —
see docs/backend/sso-keycloak-integration.md.
"""

from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

from django.core.cache import cache
import jwt
import pytest
import requests

from apps.accounts.models import SSOConfiguration
from apps.accounts.sso_config import invalidate_sso_config_cache
from shared.crypto import encrypt_secret

pytestmark = pytest.mark.django_db

ISSUER = "https://keycloak.example.com/realms/papermoon-staff"
CLIENT_ID = "papermoon-backoffice"
CLIENT_SECRET = "test-secret"


def _configure_sso(**overrides) -> SSOConfiguration:
    """Writes (and DB-persists) the SSOConfiguration singleton for a test, bypassing
    the admin view/service so these tests target oidc.py in isolation."""
    defaults = {
        "enabled": True,
        "issuer": ISSUER,
        "client_id": CLIENT_ID,
        "client_secret_encrypted": encrypt_secret(CLIENT_SECRET),
    }
    defaults.update(overrides)
    SSOConfiguration.objects.update_or_create(pk=1, defaults=defaults)
    invalidate_sso_config_cache()
    return SSOConfiguration.get_solo()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def _state_from_url(url: str) -> str:
    return parse_qs(urlsplit(url).query)["state"][0]


def _mock_token_response() -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"id_token": "fake.jwt.token"}
    return response


class TestBuildAuthorizeUrl:
    def test_raises_when_disabled(self):
        from apps.accounts.oidc import SSONotConfiguredError, build_authorize_url

        _configure_sso(enabled=False)
        with pytest.raises(SSONotConfiguredError):
            build_authorize_url()

    def test_raises_when_incomplete(self):
        from apps.accounts.oidc import SSONotConfiguredError, build_authorize_url

        _configure_sso(enabled=True, client_id="", client_secret_encrypted="")
        with pytest.raises(SSONotConfiguredError):
            build_authorize_url()

    def test_returns_authorize_url_with_pkce_and_state(self):
        from apps.accounts.oidc import build_authorize_url

        _configure_sso()
        url = build_authorize_url()
        assert url.startswith(f"{ISSUER}/protocol/openid-connect/auth?")
        query = parse_qs(urlsplit(url).query)
        assert query["client_id"] == [CLIENT_ID]
        assert query["code_challenge_method"] == ["S256"]
        assert query["response_type"] == ["code"]
        assert "code_challenge" in query
        assert "state" in query
        assert "nonce" in query

    def test_state_and_pkce_verifier_are_persisted_server_side(self):
        from apps.accounts.oidc import _STATE_CACHE_PREFIX, build_authorize_url

        _configure_sso()
        url = build_authorize_url()
        state = _state_from_url(url)

        stored = cache.get(f"{_STATE_CACHE_PREFIX}{state}")
        assert stored is not None
        assert "code_verifier" in stored
        assert "nonce" in stored
        assert stored["issuer"] == ISSUER

    def test_each_call_generates_a_distinct_state(self):
        from apps.accounts.oidc import build_authorize_url

        _configure_sso()
        first = _state_from_url(build_authorize_url())
        second = _state_from_url(build_authorize_url())
        assert first != second


class TestExchangeCode:
    def test_raises_state_invalid_when_state_unknown(self):
        from apps.accounts.oidc import SSOStateInvalidError, exchange_code

        _configure_sso()
        with pytest.raises(SSOStateInvalidError):
            exchange_code("some-code", "never-issued-state")

    def test_state_is_single_use(self):
        from apps.accounts.oidc import (
            _STATE_CACHE_PREFIX,
            SSOStateInvalidError,
            build_authorize_url,
            exchange_code,
        )

        _configure_sso()
        url = build_authorize_url()
        state = _state_from_url(url)
        nonce = cache.get(f"{_STATE_CACHE_PREFIX}{state}")["nonce"]

        with (
            patch("apps.accounts.oidc.requests.post", return_value=_mock_token_response()),
            patch("apps.accounts.oidc._get_jwks_client") as mock_jwks,
            patch("apps.accounts.oidc.jwt.decode") as mock_decode,
        ):
            mock_jwks.return_value.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")
            mock_decode.return_value = {
                "email": "staff@papermoon.com",
                "sub": "kc-sub-1",
                "nonce": nonce,
            }

            claims = exchange_code("auth-code", state)
            assert claims.email == "staff@papermoon.com"
            assert claims.subject == "kc-sub-1"

            # Replaying the same (already-consumed) state must fail — no second exchange.
            with pytest.raises(SSOStateInvalidError):
                exchange_code("auth-code", state)

    def test_token_endpoint_failure_raises_exchange_failed(self):
        from apps.accounts.oidc import SSOExchangeFailedError, build_authorize_url, exchange_code

        _configure_sso()
        state = _state_from_url(build_authorize_url())

        with patch(
            "apps.accounts.oidc.requests.post",
            side_effect=requests.ConnectionError("Keycloak unreachable"),
        ):
            with pytest.raises(SSOExchangeFailedError):
                exchange_code("auth-code", state)

    def test_missing_id_token_raises_exchange_failed(self):
        from apps.accounts.oidc import SSOExchangeFailedError, build_authorize_url, exchange_code

        _configure_sso()
        state = _state_from_url(build_authorize_url())
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {}  # no id_token

        with patch("apps.accounts.oidc.requests.post", return_value=response):
            with pytest.raises(SSOExchangeFailedError):
                exchange_code("auth-code", state)

    def test_invalid_jwt_signature_raises_exchange_failed(self):
        from apps.accounts.oidc import SSOExchangeFailedError, build_authorize_url, exchange_code

        _configure_sso()
        state = _state_from_url(build_authorize_url())

        with (
            patch("apps.accounts.oidc.requests.post", return_value=_mock_token_response()),
            patch("apps.accounts.oidc._get_jwks_client") as mock_jwks,
            patch("apps.accounts.oidc.jwt.decode", side_effect=jwt.InvalidSignatureError()),
        ):
            mock_jwks.return_value.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")
            with pytest.raises(SSOExchangeFailedError):
                exchange_code("auth-code", state)

    def test_nonce_mismatch_raises_exchange_failed(self):
        from apps.accounts.oidc import SSOExchangeFailedError, build_authorize_url, exchange_code

        _configure_sso()
        state = _state_from_url(build_authorize_url())

        with (
            patch("apps.accounts.oidc.requests.post", return_value=_mock_token_response()),
            patch("apps.accounts.oidc._get_jwks_client") as mock_jwks,
            patch("apps.accounts.oidc.jwt.decode") as mock_decode,
        ):
            mock_jwks.return_value.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")
            mock_decode.return_value = {
                "email": "staff@papermoon.com",
                "sub": "kc-sub-1",
                "nonce": "does-not-match-the-one-we-generated",
            }
            with pytest.raises(SSOExchangeFailedError):
                exchange_code("auth-code", state)

    def test_missing_email_claim_raises_exchange_failed(self):
        from apps.accounts.oidc import (
            _STATE_CACHE_PREFIX,
            SSOExchangeFailedError,
            build_authorize_url,
            exchange_code,
        )

        _configure_sso()
        url = build_authorize_url()
        state = _state_from_url(url)
        nonce = cache.get(f"{_STATE_CACHE_PREFIX}{state}")["nonce"]

        with (
            patch("apps.accounts.oidc.requests.post", return_value=_mock_token_response()),
            patch("apps.accounts.oidc._get_jwks_client") as mock_jwks,
            patch("apps.accounts.oidc.jwt.decode") as mock_decode,
        ):
            mock_jwks.return_value.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")
            mock_decode.return_value = {"sub": "kc-sub-1", "nonce": nonce}  # no email
            with pytest.raises(SSOExchangeFailedError):
                exchange_code("auth-code", state)

    def test_missing_email_falls_back_to_username_at_gov_domain(self):
        # Muitas contas do AD (contas de serviço, e a maioria dos servidores de
        # ponta — saúde, educação) não têm "mail" no AD, só "userPrincipalName"
        # (que vira a claim preferred_username) — ver docs/backend/sso-keycloak-integration.md.
        from apps.accounts.oidc import (
            _STATE_CACHE_PREFIX,
            build_authorize_url,
            exchange_code,
        )

        _configure_sso()
        url = build_authorize_url()
        state = _state_from_url(url)
        nonce = cache.get(f"{_STATE_CACHE_PREFIX}{state}")["nonce"]

        with (
            patch("apps.accounts.oidc.requests.post", return_value=_mock_token_response()),
            patch("apps.accounts.oidc._get_jwks_client") as mock_jwks,
            patch("apps.accounts.oidc.jwt.decode") as mock_decode,
        ):
            mock_jwks.return_value.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")
            mock_decode.return_value = {
                "sub": "kc-sub-1",
                "nonce": nonce,
                "preferred_username": "ADM.YURI",
            }  # no email, has preferred_username
            claims = exchange_code("auth-code", state)

        assert claims.email == "adm.yuri@rondonopolis.mt.gov.br"
        assert claims.subject == "kc-sub-1"


class TestTestIssuerConnectivity:
    def test_rejects_non_http_scheme(self):
        from apps.accounts.oidc import test_issuer_connectivity

        result = test_issuer_connectivity("not-a-url")
        assert result["reachable"] is False

    def test_connection_error_reports_unreachable(self):
        from apps.accounts.oidc import test_issuer_connectivity

        with patch(
            "apps.accounts.oidc.requests.get",
            side_effect=requests.ConnectionError("refused"),
        ):
            result = test_issuer_connectivity(ISSUER)
        assert result["reachable"] is False
        assert "refused" in result["message"]

    def test_valid_discovery_document_reports_reachable(self):
        from apps.accounts.oidc import test_issuer_connectivity

        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {
            "issuer": ISSUER,
            "authorization_endpoint": f"{ISSUER}/protocol/openid-connect/auth",
            "token_endpoint": f"{ISSUER}/protocol/openid-connect/token",
            "jwks_uri": f"{ISSUER}/protocol/openid-connect/certs",
        }
        with patch("apps.accounts.oidc.requests.get", return_value=response):
            result = test_issuer_connectivity(ISSUER)
        assert result["reachable"] is True

    def test_issuer_mismatch_is_flagged(self):
        from apps.accounts.oidc import test_issuer_connectivity

        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {
            "issuer": "https://keycloak.example.com/realms/some-other-realm",
            "authorization_endpoint": "x",
            "token_endpoint": "x",
            "jwks_uri": "x",
        }
        with patch("apps.accounts.oidc.requests.get", return_value=response):
            result = test_issuer_connectivity(ISSUER)
        assert result["reachable"] is True
        assert "não bate" in result["message"]


class TestGroupAuthorizesStaff:
    """staff_group aceita uma lista separada por vírgula (ex: TI + admins de domínio
    autorizando juntos) — ver docs/backend/sso-keycloak-integration.md."""

    def test_single_configured_group_matches(self):
        from apps.accounts.oidc import group_authorizes_staff

        assert group_authorizes_staff("papermoon-staff", ("papermoon-staff",)) is True

    def test_no_match_denies(self):
        from apps.accounts.oidc import group_authorizes_staff

        assert group_authorizes_staff("papermoon-staff", ("outro-grupo",)) is False

    def test_empty_configured_group_always_denies(self):
        from apps.accounts.oidc import group_authorizes_staff

        assert group_authorizes_staff("", ("qualquer-grupo",)) is False

    def test_leading_slash_path_is_normalized(self):
        from apps.accounts.oidc import group_authorizes_staff

        assert group_authorizes_staff("papermoon-staff", ("/papermoon-staff",)) is True

    def test_case_is_normalized(self):
        from apps.accounts.oidc import group_authorizes_staff

        assert group_authorizes_staff("Papermoon-Staff", ("papermoon-staff",)) is True

    def test_duplicated_internal_whitespace_is_normalized(self):
        # Caso real encontrado em produção: grupo sincronizado do AD com espaço
        # duplo ("Grupo TI  - HelpDesk") que é visualmente idêntico ao configurado
        # no backoffice mas byte-a-byte diferente sem a normalização.
        from apps.accounts.oidc import group_authorizes_staff

        assert group_authorizes_staff("Grupo TI - HelpDesk", ("Grupo TI  - HelpDesk",)) is True

    def test_comma_separated_list_matches_any_group(self):
        from apps.accounts.oidc import group_authorizes_staff

        configured = "Grupo Nucleo de TI,Grupo TI - Administradores,Administrators,Domain Admins"
        assert group_authorizes_staff(configured, ("Domain Admins",)) is True
        assert group_authorizes_staff(configured, ("/Administrators",)) is True
        assert group_authorizes_staff(configured, ("Financeiro",)) is False

    def test_user_with_multiple_groups_matches_if_any_is_allowed(self):
        from apps.accounts.oidc import group_authorizes_staff

        configured = "Grupo Nucleo de TI,Administrators"
        token_groups = ("Financeiro", "Grupo Nucleo de TI", "RH")
        assert group_authorizes_staff(configured, token_groups) is True
