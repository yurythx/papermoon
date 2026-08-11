"""
Integration tests for the admin-editable central Keycloak connection surface:
- GET/PATCH /api/v1/admin/keycloak-connection/
- POST /api/v1/admin/keycloak-connection/test/

Espelha tests/integration/test_sso_config_admin.py — mesmo padrão de teste,
conexão diferente (provisionamento de clientes, não SSO de staff).
"""

from unittest.mock import patch

from django.core.cache import cache
import pytest

CONFIG_URL = "/api/v1/admin/keycloak-connection/"
TEST_URL = "/api/v1/admin/keycloak-connection/test/"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestKeycloakConnectionAdminView:
    def test_get_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(CONFIG_URL)
        assert resp.status_code == 401

    def test_get_non_admin_returns_403(self, customer_client):
        resp = customer_client.get(CONFIG_URL)
        assert resp.status_code == 403

    def test_get_default_state(self, admin_client):
        resp = admin_client.get(CONFIG_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enabled"] is False
        assert data["admin_token_set"] is False
        assert data["api_url"] == ""

    def test_patch_enable_with_all_fields_succeeds(self, admin_client):
        resp = admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "api_url": "https://keycloak.example.com",
                "admin_token": "s3cr3t-token",
            },
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enabled"] is True
        assert data["admin_token_set"] is True
        assert "s3cr3t-token" not in resp.content.decode()

    def test_patch_enable_without_api_url_returns_400(self, admin_client):
        resp = admin_client.patch(
            CONFIG_URL, {"enabled": True, "admin_token": "tok"}, format="json"
        )
        assert resp.status_code == 400

    def test_patch_enable_without_token_and_none_saved_returns_400(self, admin_client):
        resp = admin_client.patch(
            CONFIG_URL,
            {"enabled": True, "api_url": "https://keycloak.example.com"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "validation_error"

    def test_patch_blank_token_keeps_previously_saved_token(self, admin_client):
        from apps.provisioning.models import KeycloakConnection
        from shared.crypto import decrypt_secret

        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "api_url": "https://keycloak.example.com",
                "admin_token": "original-token",
            },
            format="json",
        )
        resp = admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "api_url": "https://keycloak.example.com/renamed",
                "admin_token": "",
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["admin_token_set"] is True
        assert resp.json()["data"]["api_url"] == "https://keycloak.example.com/renamed"

        row = KeycloakConnection.get_solo()
        assert decrypt_secret(row.admin_token_encrypted) == "original-token"

    def test_patch_writes_audit_log_without_leaking_token(self, admin_client):
        from apps.audit.models import AuditLog

        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "api_url": "https://keycloak.example.com",
                "admin_token": "s3cr3t-token",
            },
            format="json",
        )
        entry = AuditLog.objects.filter(action="keycloak_connection.updated").first()
        assert entry is not None
        assert entry.changes["admin_token_changed"] is True
        assert "s3cr3t-token" not in str(entry.changes)

    def test_patch_disable_does_not_require_api_url(self, admin_client):
        resp = admin_client.patch(CONFIG_URL, {"enabled": False}, format="json")
        assert resp.status_code == 200
        assert resp.json()["data"]["enabled"] is False

    def test_patch_disable_with_only_enabled_field_preserves_api_url(self, admin_client):
        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "api_url": "https://keycloak.example.com",
                "admin_token": "s3cr3t-token",
            },
            format="json",
        )
        resp = admin_client.patch(CONFIG_URL, {"enabled": False}, format="json")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enabled"] is False
        assert data["api_url"] == "https://keycloak.example.com"
        assert data["admin_token_set"] is True


@pytest.mark.django_db
class TestKeycloakConnectionTestView:
    def test_non_admin_returns_403(self, customer_client):
        resp = customer_client.post(
            TEST_URL, {"api_url": "https://x.example.com", "admin_token": "t"}, format="json"
        )
        assert resp.status_code == 403

    def test_missing_api_url_and_none_saved_returns_400(self, admin_client):
        resp = admin_client.post(TEST_URL, {}, format="json")
        assert resp.status_code == 400

    def test_missing_token_and_none_saved_returns_400(self, admin_client):
        resp = admin_client.post(
            TEST_URL, {"api_url": "https://keycloak.example.com"}, format="json"
        )
        assert resp.status_code == 400

    def test_delegates_to_connectivity_check(self, admin_client):
        with patch(
            "apps.provisioning.views_admin.test_admin_connectivity",
            return_value={"reachable": True, "message": "ok"},
        ) as mock_check:
            resp = admin_client.post(
                TEST_URL,
                {"api_url": "https://keycloak.example.com", "admin_token": "tok"},
                format="json",
            )
        assert resp.status_code == 200
        assert resp.json()["data"] == {"reachable": True, "message": "ok"}
        mock_check.assert_called_once_with("https://keycloak.example.com", "tok")

    def test_falls_back_to_saved_values_when_omitted(self, admin_client):
        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "api_url": "https://keycloak.example.com/saved",
                "admin_token": "saved-token",
            },
            format="json",
        )
        with patch(
            "apps.provisioning.views_admin.test_admin_connectivity",
            return_value={"reachable": True, "message": "ok"},
        ) as mock_check:
            resp = admin_client.post(TEST_URL, {}, format="json")
        assert resp.status_code == 200
        mock_check.assert_called_once_with("https://keycloak.example.com/saved", "saved-token")
