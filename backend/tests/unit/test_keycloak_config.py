"""
Unit tests for apps/provisioning/keycloak_config.py — a conexão central do
PaperMoon com o Keycloak que ele administra (provisionamento). Espelha
tests/unit/test_accounts_oidc.py no padrão de cache (autouse clear_cache).
"""

from unittest.mock import MagicMock, patch

from django.core.cache import cache
import pytest
import requests

from apps.provisioning.keycloak_config import (
    KeycloakConnectionConfig,
    get_keycloak_connection,
    invalidate_keycloak_connection_cache,
    open_admin_session,
    update_keycloak_connection,
)

# Apelidado no import: um nome começando com "test_" no escopo do módulo é
# coletado pelo pytest como função de teste solta (python_functions = test_*
# no pytest.ini) — precisa ficar fora desse padrão pra não virar um teste
# "fantasma" com fixtures erradas.
from apps.provisioning.keycloak_config import test_admin_connectivity as check_admin_connectivity
from apps.provisioning.models import KeycloakConnection
from shared.crypto import decrypt_secret, encrypt_secret

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def _configure(**overrides) -> KeycloakConnection:
    defaults = {
        "enabled": True,
        "api_url": "https://keycloak.example.com",
        "admin_token_encrypted": encrypt_secret("admin-tok"),
    }
    defaults.update(overrides)
    KeycloakConnection.objects.update_or_create(pk=1, defaults=defaults)
    invalidate_keycloak_connection_cache()
    return KeycloakConnection.get_solo()


class TestKeycloakConnectionConfigIsUsable:
    def test_usable_when_enabled_with_url_and_token(self):
        config = KeycloakConnectionConfig(
            enabled=True, api_url="https://x.example.com", admin_token="tok"
        )
        assert config.is_usable is True

    def test_not_usable_when_disabled(self):
        config = KeycloakConnectionConfig(
            enabled=False, api_url="https://x.example.com", admin_token="tok"
        )
        assert config.is_usable is False

    def test_not_usable_without_api_url(self):
        config = KeycloakConnectionConfig(enabled=True, api_url="", admin_token="tok")
        assert config.is_usable is False

    def test_not_usable_without_admin_token(self):
        config = KeycloakConnectionConfig(
            enabled=True, api_url="https://x.example.com", admin_token=""
        )
        assert config.is_usable is False


class TestGetKeycloakConnection:
    def test_reads_from_solo_row_and_decrypts_token(self):
        _configure(
            api_url="https://keycloak.example.com", admin_token_encrypted=encrypt_secret("s3cr3t")
        )
        config = get_keycloak_connection()
        assert config.enabled is True
        assert config.api_url == "https://keycloak.example.com"
        assert config.admin_token == "s3cr3t"

    def test_default_state_is_disabled_and_empty(self):
        config = get_keycloak_connection()
        assert config.enabled is False
        assert config.api_url == ""
        assert config.admin_token == ""

    def test_result_is_cached_until_invalidated(self):
        _configure(api_url="https://first.example.com")
        first = get_keycloak_connection()
        assert first.api_url == "https://first.example.com"

        # Muda o banco sem invalidar o cache — get_keycloak_connection() deve
        # continuar devolvendo o valor cacheado (mesmo padrão de get_sso_config).
        KeycloakConnection.objects.update(api_url="https://second.example.com")
        cached = get_keycloak_connection()
        assert cached.api_url == "https://first.example.com"

        invalidate_keycloak_connection_cache()
        fresh = get_keycloak_connection()
        assert fresh.api_url == "https://second.example.com"


class TestUpdateKeycloakConnection:
    def test_sets_all_fields_and_invalidates_cache(self, admin_user):
        get_keycloak_connection()  # popula o cache com o estado default

        row = update_keycloak_connection(
            enabled=True,
            api_url="https://keycloak.example.com/",
            admin_token="tok-123",
            user=admin_user,
        )
        assert row.enabled is True
        assert row.api_url == "https://keycloak.example.com"  # barra final removida
        assert decrypt_secret(row.admin_token_encrypted) == "tok-123"
        assert row.updated_by_id == admin_user.id

        # Cache foi invalidado — a próxima leitura reflete o valor novo.
        assert get_keycloak_connection().api_url == "https://keycloak.example.com"

    def test_blank_token_keeps_previously_saved_token(self, admin_user):
        update_keycloak_connection(
            enabled=True,
            api_url="https://keycloak.example.com",
            admin_token="original-token",
            user=admin_user,
        )
        row = update_keycloak_connection(
            enabled=True,
            api_url="https://keycloak.example.com",
            admin_token="",
            user=admin_user,
        )
        assert decrypt_secret(row.admin_token_encrypted) == "original-token"

    def test_none_token_keeps_previously_saved_token(self, admin_user):
        update_keycloak_connection(
            enabled=True,
            api_url="https://keycloak.example.com",
            admin_token="original-token",
            user=admin_user,
        )
        row = update_keycloak_connection(
            enabled=True,
            api_url="https://keycloak.example.com",
            admin_token=None,
            user=admin_user,
        )
        assert decrypt_secret(row.admin_token_encrypted) == "original-token"


class TestOpenAdminSession:
    def test_returns_none_when_not_usable(self):
        session, api_url = open_admin_session()
        assert session is None
        assert api_url == ""

    def test_returns_session_with_bearer_header_when_usable(self):
        _configure(admin_token_encrypted=encrypt_secret("tok-abc"))
        session, api_url = open_admin_session()
        assert session is not None
        assert api_url == "https://keycloak.example.com"
        assert session.headers["Authorization"] == "Bearer tok-abc"
        assert session.headers["Content-Type"] == "application/json"


class TestTestAdminConnectivity:
    def test_invalid_url_returns_not_reachable(self):
        result = check_admin_connectivity("not-a-url", "tok")
        assert result["reachable"] is False

    def test_connection_error_returns_not_reachable(self):
        with patch(
            "apps.provisioning.keycloak_config.requests.get",
            side_effect=requests.ConnectionError("boom"),
        ):
            result = check_admin_connectivity("https://keycloak.example.com", "tok")
        assert result["reachable"] is False
        assert "conectar" in result["message"].lower()

    def test_401_returns_reachable_but_token_refused(self):
        mock_resp = MagicMock(status_code=401, ok=False)
        with patch("apps.provisioning.keycloak_config.requests.get", return_value=mock_resp):
            result = check_admin_connectivity("https://keycloak.example.com", "bad-tok")
        assert result["reachable"] is True
        assert "recusad" in result["message"].lower()

    def test_403_returns_reachable_but_token_refused(self):
        mock_resp = MagicMock(status_code=403, ok=False)
        with patch("apps.provisioning.keycloak_config.requests.get", return_value=mock_resp):
            result = check_admin_connectivity("https://keycloak.example.com", "bad-tok")
        assert result["reachable"] is True

    def test_other_error_status_returns_reachable_with_error_message(self):
        mock_resp = MagicMock(status_code=500, ok=False)
        with patch("apps.provisioning.keycloak_config.requests.get", return_value=mock_resp):
            result = check_admin_connectivity("https://keycloak.example.com", "tok")
        assert result["reachable"] is True
        assert "500" in result["message"]

    def test_200_with_realm_list_returns_count(self):
        mock_resp = MagicMock(status_code=200, ok=True)
        mock_resp.json.return_value = [{"realm": "a"}, {"realm": "b"}]
        with patch("apps.provisioning.keycloak_config.requests.get", return_value=mock_resp):
            result = check_admin_connectivity("https://keycloak.example.com", "tok")
        assert result["reachable"] is True
        assert "2 realm" in result["message"]

    def test_200_with_non_json_body_is_still_reachable(self):
        mock_resp = MagicMock(status_code=200, ok=True)
        mock_resp.json.side_effect = ValueError("not json")
        with patch("apps.provisioning.keycloak_config.requests.get", return_value=mock_resp):
            result = check_admin_connectivity("https://keycloak.example.com", "tok")
        assert result["reachable"] is True
