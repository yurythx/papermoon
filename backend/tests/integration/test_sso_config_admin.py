"""
Integration tests for the admin-editable SSO configuration surface:
- GET/PATCH /api/v1/admin/sso-config/
- POST /api/v1/admin/sso-config/test/
- GET /api/v1/auth/sso/status/ (public)

See docs/backend/sso-keycloak-integration.md.
"""

from unittest.mock import patch

import pytest

CONFIG_URL = "/api/v1/admin/sso-config/"
TEST_URL = "/api/v1/admin/sso-config/test/"
STATUS_URL = "/api/v1/auth/sso/status/"


@pytest.mark.django_db
class TestSSOConfigAdminView:
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
        assert data["client_secret_set"] is False
        assert data["redirect_uri"].endswith("/api/auth/sso/callback")

    def test_patch_enable_with_all_fields_succeeds(self, admin_client):
        resp = admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon-staff",
                "client_id": "papermoon-backoffice",
                "client_secret": "s3cr3t",
            },
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enabled"] is True
        assert data["client_secret_set"] is True
        # Secret itself must never come back in the response.
        assert "s3cr3t" not in resp.content.decode()

    def test_patch_enable_without_issuer_returns_400(self, admin_client):
        resp = admin_client.patch(
            CONFIG_URL,
            {"enabled": True, "client_id": "x", "client_secret": "s3cr3t"},
            format="json",
        )
        assert resp.status_code == 400

    def test_patch_enable_without_secret_and_none_saved_returns_400(self, admin_client):
        resp = admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon-staff",
                "client_id": "papermoon-backoffice",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "validation_error"

    def test_patch_blank_secret_keeps_previously_saved_secret(self, admin_client):
        from apps.accounts.models import SSOConfiguration
        from shared.crypto import decrypt_secret

        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon-staff",
                "client_id": "papermoon-backoffice",
                "client_secret": "original-secret",
            },
            format="json",
        )

        resp = admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon-staff",
                "client_id": "papermoon-backoffice-renamed",
                "client_secret": "",
            },
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["client_secret_set"] is True
        assert resp.json()["data"]["client_id"] == "papermoon-backoffice-renamed"

        row = SSOConfiguration.get_solo()
        assert decrypt_secret(row.client_secret_encrypted) == "original-secret"

    def test_patch_writes_audit_log_without_leaking_secret(self, admin_client):
        from apps.audit.models import AuditLog

        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon-staff",
                "client_id": "papermoon-backoffice",
                "client_secret": "s3cr3t",
            },
            format="json",
        )
        entry = AuditLog.objects.filter(action="sso_config.updated").first()
        assert entry is not None
        assert entry.changes["client_secret_changed"] is True
        assert "s3cr3t" not in str(entry.changes)

    def test_patch_disable_does_not_require_issuer(self, admin_client):
        resp = admin_client.patch(CONFIG_URL, {"enabled": False}, format="json")
        assert resp.status_code == 200
        assert resp.json()["data"]["enabled"] is False

    def test_patch_disable_with_only_enabled_field_preserves_issuer_and_client_id(
        self, admin_client
    ):
        """Regressão: PATCH {"enabled": false} sozinho não pode apagar issuer/client_id —
        campos ausentes do body devem manter o valor já salvo, não resetar pra "" ."""
        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon-staff",
                "client_id": "papermoon-backoffice",
                "client_secret": "s3cr3t",
            },
            format="json",
        )

        resp = admin_client.patch(CONFIG_URL, {"enabled": False}, format="json")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enabled"] is False
        assert data["issuer"] == "https://keycloak.example.com/realms/papermoon-staff"
        assert data["client_id"] == "papermoon-backoffice"
        assert data["client_secret_set"] is True


@pytest.mark.django_db
class TestSSOConfigTestView:
    def test_non_admin_returns_403(self, customer_client):
        resp = customer_client.post(TEST_URL, {"issuer": "https://x.example.com"}, format="json")
        assert resp.status_code == 403

    def test_missing_issuer_and_none_saved_returns_400(self, admin_client):
        resp = admin_client.post(TEST_URL, {}, format="json")
        assert resp.status_code == 400

    def test_delegates_to_connectivity_check(self, admin_client):
        with patch(
            "apps.accounts.views.test_issuer_connectivity",
            return_value={"reachable": True, "message": "ok"},
        ) as mock_check:
            resp = admin_client.post(
                TEST_URL, {"issuer": "https://keycloak.example.com/realms/x"}, format="json"
            )
        assert resp.status_code == 200
        assert resp.json()["data"] == {"reachable": True, "message": "ok"}
        mock_check.assert_called_once_with("https://keycloak.example.com/realms/x")

    def test_falls_back_to_saved_issuer_when_omitted(self, admin_client):
        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/saved",
                "client_id": "papermoon-backoffice",
                "client_secret": "s3cr3t",
            },
            format="json",
        )
        with patch(
            "apps.accounts.views.test_issuer_connectivity",
            return_value={"reachable": True, "message": "ok"},
        ) as mock_check:
            resp = admin_client.post(TEST_URL, {}, format="json")
        assert resp.status_code == 200
        mock_check.assert_called_once_with("https://keycloak.example.com/realms/saved")


@pytest.mark.django_db
class TestSSOStatusView:
    def test_public_status_reflects_enabled_flag(self, api_client, admin_client):
        assert api_client.get(STATUS_URL).json()["data"]["enabled"] is False

        admin_client.patch(
            CONFIG_URL,
            {
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon-staff",
                "client_id": "papermoon-backoffice",
                "client_secret": "s3cr3t",
            },
            format="json",
        )

        assert api_client.get(STATUS_URL).json()["data"]["enabled"] is True

    def test_status_does_not_require_authentication(self, api_client):
        resp = api_client.get(STATUS_URL)
        assert resp.status_code == 200
