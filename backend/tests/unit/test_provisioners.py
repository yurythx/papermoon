"""
Unit tests for apps/provisioning/{chatwoot,n8n,meta_api}.py.
HTTP calls are mocked via unittest.mock. The "disabled" (no credentials) paths
are exercised by leaving settings blank.
"""

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chatwoot_provisioner(enabled=False):
    from apps.provisioning.chatwoot import ChatwootProvisioner

    p = ChatwootProvisioner.__new__(ChatwootProvisioner)
    p._enabled = enabled
    if enabled:
        mock_client = MagicMock()
        p._client = mock_client
        return p, mock_client
    return p, None


def _make_n8n_provisioner(enabled=False):
    from apps.provisioning.n8n import N8nProvisioner

    p = N8nProvisioner.__new__(N8nProvisioner)
    p._enabled = enabled
    if enabled:
        p._base_url = "https://n8n.example.com"
        mock_session = MagicMock()
        p._session = mock_session
        return p, mock_session
    return p, None


def _make_meta_provisioner(enabled=False):
    from apps.provisioning.meta_api import MetaWhatsAppProvisioner

    p = MetaWhatsAppProvisioner.__new__(MetaWhatsAppProvisioner)
    p._token = "tok" if enabled else ""
    p._waba_id = "waba-1" if enabled else ""
    p._enabled = enabled
    if enabled:
        mock_session = MagicMock()
        p._session = mock_session
        return p, mock_session
    return p, None


def _make_glpi_provisioner(enabled=False):
    from apps.provisioning.glpi import GLPIProvisioner

    p = GLPIProvisioner.__new__(GLPIProvisioner)
    p._enabled = enabled
    if enabled:
        p._base_url = "https://glpi.example.com"
        p._session = MagicMock()
        p._init_session = MagicMock(return_value="session-1")
        p._kill_session = MagicMock()
        return p, p._session
    return p, None


def _make_truenas_provisioner(enabled=False):
    from apps.provisioning.truenas import TrueNASProvisioner

    p = TrueNASProvisioner.__new__(TrueNASProvisioner)
    p._enabled = enabled
    if enabled:
        p._base_url = "https://truenas.example.com"
        p._pool = "data"
        p._session = MagicMock()
        return p, p._session
    return p, None


def _make_zabbix_provisioner(enabled=False):
    from apps.provisioning.zabbix import ZabbixProvisioner

    p = ZabbixProvisioner.__new__(ZabbixProvisioner)
    p._enabled = enabled
    if enabled:
        p._call = MagicMock(return_value={"userids": ["zabbix-user-1"]})
        return p, p._call
    return p, None


# ---------------------------------------------------------------------------
# ChatwootProvisioner — disabled paths (no credentials)
# ---------------------------------------------------------------------------


class TestChatwootProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        p, _ = _make_chatwoot_provisioner(enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("chatwoot_stub_")

    def test_suspend_noop(self):
        p, _ = _make_chatwoot_provisioner(enabled=False)
        p.suspend("ext-1", "cust-1")

    def test_reactivate_noop(self):
        p, _ = _make_chatwoot_provisioner(enabled=False)
        p.reactivate("ext-1", "cust-1")

    def test_deprovision_noop(self):
        p, _ = _make_chatwoot_provisioner(enabled=False)
        p.deprovision("ext-1", "cust-1")


# ---------------------------------------------------------------------------
# ChatwootProvisioner — enabled paths (client calls mocked)
# ---------------------------------------------------------------------------


class TestChatwootProvisionerEnabled:
    def test_provision_returns_external_id_from_response(self):
        p, mock_client = _make_chatwoot_provisioner(enabled=True)
        mock_client.provision_customer.return_value = {"id": "chatwoot-acct-99"}

        result = p.provision("cust-1", "sa-1", {})
        assert result == "chatwoot-acct-99"
        mock_client.provision_customer.assert_called_once_with("cust-1")

    def test_provision_falls_back_to_customer_id_when_no_id_in_response(self):
        p, mock_client = _make_chatwoot_provisioner(enabled=True)
        mock_client.provision_customer.return_value = {}

        result = p.provision("cust-xyz", "sa-1", {})
        assert result == "cust-xyz"

    def test_suspend_calls_client(self):
        p, mock_client = _make_chatwoot_provisioner(enabled=True)
        p.suspend("ext-1", "cust-1")
        mock_client.suspend_agents.assert_called_once_with("cust-1")

    def test_reactivate_calls_client(self):
        p, mock_client = _make_chatwoot_provisioner(enabled=True)
        p.reactivate("ext-1", "cust-1")
        mock_client.reactivate_agents.assert_called_once_with("cust-1")

    def test_deprovision_suspends_agents(self):
        p, mock_client = _make_chatwoot_provisioner(enabled=True)
        p.deprovision("ext-1", "cust-1")
        mock_client.suspend_agents.assert_called_once_with("cust-1")


# ---------------------------------------------------------------------------
# N8nProvisioner — disabled paths (no credentials)
# ---------------------------------------------------------------------------


class TestN8nProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        p, _ = _make_n8n_provisioner(enabled=False)
        result = p.provision("cust-abc123", "sa-1", {})
        assert result.startswith("n8n_stub_")

    def test_suspend_noop(self):
        p, _ = _make_n8n_provisioner(enabled=False)
        p.suspend("ext-1", "cust-1")  # Should not raise

    def test_reactivate_noop(self):
        p, _ = _make_n8n_provisioner(enabled=False)
        p.reactivate("ext-1", "cust-1")  # Should not raise

    def test_deprovision_noop(self):
        p, _ = _make_n8n_provisioner(enabled=False)
        p.deprovision("ext-1", "cust-1")  # Should not raise


# ---------------------------------------------------------------------------
# N8nProvisioner — enabled paths (HTTP calls mocked)
# ---------------------------------------------------------------------------


class TestN8nProvisionerEnabled:
    def test_provision_creates_user_and_returns_id(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [{"id": "n8n-user-1"}]
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-123", "sa-1", {"admin_email": "admin@test.com"})
        assert result == "n8n-user-1"

    def test_provision_falls_back_when_response_empty(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = []
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("n8n_")

    def test_suspend_patches_role(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.patch.return_value = mock_resp

        p.suspend("ext-user-1", "cust-1")
        mock_session.patch.assert_called_once()

    def test_suspend_ignores_404(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.patch.return_value = mock_resp

        p.suspend("ext-user-1", "cust-1")  # Should not raise

    def test_reactivate_patches_role(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.patch.return_value = mock_resp

        p.reactivate("ext-user-1", "cust-1")
        mock_session.patch.assert_called_once()

    def test_deprovision_deletes_user(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.delete.return_value = mock_resp

        p.deprovision("ext-user-1", "cust-1")
        mock_session.delete.assert_called_once()

    def test_deprovision_ignores_404(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.delete.return_value = mock_resp

        p.deprovision("ext-user-1", "cust-1")  # Should not raise

    def test_provision_uses_papermoon_default_email(self):
        p, mock_session = _make_n8n_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [{"id": "n8n-user-1"}]
        mock_session.post.return_value = mock_resp

        p.provision("abcdefgh123", "sa-1", {})

        payload = mock_session.post.call_args.kwargs["json"][0]
        assert payload["email"] == "n8n_abcdefgh@tenants.papermoon.com"


class TestProvisionerPaperMoonDefaults:
    def test_glpi_provision_uses_papermoon_login_and_email_defaults(self):
        p, mock_session = _make_glpi_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"id": "glpi-user-1"}
        mock_session.post.return_value = mock_resp

        p.provision("abcdefgh123", "sa-1", {})

        payload = mock_session.post.call_args.kwargs["json"]["input"]
        assert payload["name"] == "papermoon_abcdefgh"
        assert payload["email"] == "glpi_abcdefgh@tenants.papermoon.com"

    def test_truenas_provision_uses_papermoon_slug_and_email_defaults(self):
        p, mock_session = _make_truenas_provisioner(enabled=True)
        dataset_resp = MagicMock()
        dataset_resp.raise_for_status.return_value = None
        user_resp = MagicMock()
        user_resp.raise_for_status.return_value = None
        user_resp.json.return_value = {"id": "user-1"}
        mock_session.post.side_effect = [dataset_resp, user_resp, MagicMock()]

        p.provision("abcdefgh123", "sa-1", {})

        first_call = mock_session.post.call_args_list[0]
        second_call = mock_session.post.call_args_list[1]
        assert first_call.kwargs["json"]["name"] == "data/papermoon_abcdefgh"
        assert second_call.kwargs["json"]["username"] == "papermoon_abcdefgh"
        assert second_call.kwargs["json"]["email"] == "papermoon_abcdefgh@tenants.papermoon.com"

    def test_truenas_deprovision_uses_papermoon_slug(self):
        p, mock_session = _make_truenas_provisioner(enabled=True)
        first_delete = MagicMock()
        first_delete.status_code = 204
        second_delete = MagicMock()
        second_delete.status_code = 204
        mock_session.delete.side_effect = [first_delete, second_delete]

        p.deprovision("user-1", "abcdefgh123")

        dataset_delete_url = mock_session.delete.call_args_list[1].args[0]
        assert "data%2Fpapermoon_abcdefgh" in dataset_delete_url

    def test_zabbix_provision_uses_papermoon_alias_default(self):
        p, mock_call = _make_zabbix_provisioner(enabled=True)

        p.provision("abcdefgh123", "sa-1", {})

        params = mock_call.call_args.args[1]
        assert params["alias"] == "papermoon_abcdefgh"
        assert params["name"] == "papermoon_abcdefgh"


# ---------------------------------------------------------------------------
# MetaWhatsAppProvisioner — disabled paths
# ---------------------------------------------------------------------------


class TestMetaProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        p, _ = _make_meta_provisioner(enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("waba_stub_")

    def test_suspend_noop(self):
        p, _ = _make_meta_provisioner(enabled=False)
        p.suspend("ext-1", "cust-1")

    def test_reactivate_noop(self):
        p, _ = _make_meta_provisioner(enabled=False)
        p.reactivate("ext-1", "cust-1")

    def test_deprovision_noop(self):
        p, _ = _make_meta_provisioner(enabled=False)
        p.deprovision("ext-1", "cust-1")


# ---------------------------------------------------------------------------
# MetaWhatsAppProvisioner — enabled paths
# ---------------------------------------------------------------------------


class TestMetaProvisionerEnabled:
    def test_provision_uses_phone_number_from_config(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-1", "sa-1", {"phone_number_id": "phone-99"})
        assert result == "phone-99"
        mock_session.post.assert_called_once()

    def test_provision_picks_phone_when_not_in_config(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        # _pick_phone_number call
        pick_resp = MagicMock()
        pick_resp.raise_for_status.return_value = None
        pick_resp.json.return_value = {
            "data": [{"id": "phone-77", "code_verification_status": "NOT_VERIFIED"}]
        }
        # register call
        reg_resp = MagicMock()
        reg_resp.raise_for_status.return_value = None
        mock_session.get.return_value = pick_resp
        mock_session.post.return_value = reg_resp

        result = p.provision("cust-1", "sa-1", {})
        assert result == "phone-77"

    def test_provision_raises_when_no_phone_available(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        pick_resp = MagicMock()
        pick_resp.raise_for_status.return_value = None
        pick_resp.json.return_value = {"data": []}  # no numbers
        mock_session.get.return_value = pick_resp

        with pytest.raises(RuntimeError, match="No available phone number"):
            p.provision("cust-1", "sa-1", {})

    def test_suspend_deregisters_number(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.post.return_value = mock_resp

        p.suspend("phone-1", "cust-1")
        mock_session.post.assert_called_once()

    def test_suspend_ignores_404(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.post.return_value = mock_resp

        p.suspend("phone-1", "cust-1")  # no raise

    def test_reactivate_registers_number(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.post.return_value = mock_resp

        p.reactivate("phone-1", "cust-1")
        mock_session.post.assert_called_once()

    def test_deprovision_deregisters_number(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.post.return_value = mock_resp

        p.deprovision("phone-1", "cust-1")
        mock_session.post.assert_called_once()

    def test_pick_phone_returns_none_when_all_verified(self):
        p, mock_session = _make_meta_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "data": [{"id": "phone-1", "code_verification_status": "VERIFIED"}]
        }
        mock_session.get.return_value = mock_resp

        result = p._pick_phone_number()
        assert result is None


# ---------------------------------------------------------------------------
# RustDeskProvisioner — helpers
# ---------------------------------------------------------------------------


def _make_rustdesk_provisioner(enabled=False):
    from apps.provisioning.rustdesk import RustDeskProvisioner

    p = RustDeskProvisioner.__new__(RustDeskProvisioner)
    p._enabled = enabled
    if enabled:
        p._api_url = "https://rustdesk.example.com"
        mock_session = MagicMock()
        p._session = mock_session
        return p, mock_session
    return p, None


# ---------------------------------------------------------------------------
# RustDeskProvisioner — disabled paths (no credentials)
# ---------------------------------------------------------------------------


class TestRustDeskProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        p, _ = _make_rustdesk_provisioner(enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("rustdesk_stub_")

    def test_suspend_noop(self):
        p, _ = _make_rustdesk_provisioner(enabled=False)
        p.suspend("ext-1", "cust-1")  # Should not raise

    def test_reactivate_noop(self):
        p, _ = _make_rustdesk_provisioner(enabled=False)
        p.reactivate("ext-1", "cust-1")  # Should not raise

    def test_deprovision_noop(self):
        p, _ = _make_rustdesk_provisioner(enabled=False)
        p.deprovision("ext-1", "cust-1")  # Should not raise


# ---------------------------------------------------------------------------
# RustDeskProvisioner — enabled paths (HTTP calls mocked)
# ---------------------------------------------------------------------------


class TestRustDeskProvisionerEnabled:
    def test_provision_creates_user_and_returns_guid(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"guid": "rustdesk-guid-99"}
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-123", "sa-1", {"admin_email": "admin@test.com"})
        assert result == "rustdesk-guid-99"
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args
        assert "/api/user" in call_kwargs[0][0]

    def test_provision_falls_back_to_id_when_no_guid(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"id": "rustdesk-id-77"}
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-123", "sa-1", {})
        assert result == "rustdesk-id-77"

    def test_provision_falls_back_to_customer_id_when_no_id_or_guid(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {}
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result == "cust-abc"  # first 8 chars, but falls through to [:8]

    def test_provision_sends_status_1_active(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"guid": "g1"}
        mock_session.post.return_value = mock_resp

        p.provision("cust-1", "sa-1", {})
        payload = mock_session.post.call_args[1]["json"]
        assert payload["status"] == 1

    def test_suspend_sends_status_2_disabled(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.put.return_value = mock_resp

        p.suspend("guid-1", "cust-1")
        payload = mock_session.put.call_args[1]["json"]
        assert payload["status"] == 2
        assert "guid-1" in mock_session.put.call_args[0][0]

    def test_suspend_ignores_404(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.put.return_value = mock_resp

        p.suspend("guid-1", "cust-1")  # Should not raise

    def test_reactivate_sends_status_1_active(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session.put.return_value = mock_resp

        p.reactivate("guid-1", "cust-1")
        payload = mock_session.put.call_args[1]["json"]
        assert payload["status"] == 1

    def test_reactivate_ignores_404(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.put.return_value = mock_resp

        p.reactivate("guid-1", "cust-1")  # Should not raise

    def test_deprovision_deletes_user(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.delete.return_value = mock_resp

        p.deprovision("guid-1", "cust-1")
        mock_session.delete.assert_called_once()
        assert "guid-1" in mock_session.delete.call_args[0][0]

    def test_deprovision_ignores_404(self):
        p, mock_session = _make_rustdesk_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.delete.return_value = mock_resp

        p.deprovision("guid-1", "cust-1")  # Should not raise

    def test_generate_password_produces_nonempty_string(self):
        from apps.provisioning.rustdesk import RustDeskProvisioner

        pwd = RustDeskProvisioner._generate_password()
        assert isinstance(pwd, str) and len(pwd) > 0


# ---------------------------------------------------------------------------
# registry — RustDesk is registered
# ---------------------------------------------------------------------------


class TestRustDeskRegistry:
    def test_get_provisioner_returns_rustdesk(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}  # force rebuild
        provisioner = registry.get_provisioner("rustdesk")
        assert provisioner is not None
        assert provisioner.service_key == "rustdesk"


# ---------------------------------------------------------------------------
# Helpers — WindowsServer & Samba
# ---------------------------------------------------------------------------


def _make_windows_server_provisioner(enabled=False):
    from apps.provisioning.windows_server import WindowsServerProvisioner

    p = WindowsServerProvisioner.__new__(WindowsServerProvisioner)
    p._wac_url = "https://wac.example.com" if enabled else ""
    p._wac_key = "secret" if enabled else ""
    p._enabled = enabled
    return p


def _make_samba_provisioner(enabled=False):
    from apps.provisioning.samba import SambaProvisioner

    p = SambaProvisioner.__new__(SambaProvisioner)
    p._api_url = "https://samba.example.com" if enabled else ""
    p._api_key = "secret" if enabled else ""
    p._enabled = enabled
    return p


# ---------------------------------------------------------------------------
# WindowsServerProvisioner — disabled (no credentials)
# ---------------------------------------------------------------------------


class TestWindowsServerProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        p = _make_windows_server_provisioner(enabled=False)
        result = p.provision("cust-uuid-1", "sa-1", {})
        assert result.startswith("winserver_stub_")

    def test_suspend_is_noop(self):
        p = _make_windows_server_provisioner(enabled=False)
        p.suspend("ext-1", "cust-1")  # Should not raise

    def test_reactivate_is_noop(self):
        p = _make_windows_server_provisioner(enabled=False)
        p.reactivate("ext-1", "cust-1")  # Should not raise

    def test_deprovision_is_noop(self):
        p = _make_windows_server_provisioner(enabled=False)
        p.deprovision("ext-1", "cust-1")  # Should not raise


# ---------------------------------------------------------------------------
# WindowsServerProvisioner — enabled
# ---------------------------------------------------------------------------


class TestWindowsServerProvisionerEnabled:
    def test_provision_returns_prefixed_id(self):
        p = _make_windows_server_provisioner(enabled=True)
        result = p.provision("cust-uuid-1", "sa-1", {})
        assert result.startswith("winserver_")

    def test_suspend_logs_without_raising(self):
        p = _make_windows_server_provisioner(enabled=True)
        p.suspend("ext-1", "cust-1")

    def test_reactivate_logs_without_raising(self):
        p = _make_windows_server_provisioner(enabled=True)
        p.reactivate("ext-1", "cust-1")

    def test_deprovision_logs_without_raising(self):
        p = _make_windows_server_provisioner(enabled=True)
        p.deprovision("ext-1", "cust-1")


# ---------------------------------------------------------------------------
# registry — WindowsServer is registered
# ---------------------------------------------------------------------------


class TestWindowsServerRegistry:
    def test_get_provisioner_returns_windows_server(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("windows-server")
        assert provisioner is not None
        assert provisioner.service_key == "windows-server"


# ---------------------------------------------------------------------------
# SambaProvisioner — disabled (no credentials)
# ---------------------------------------------------------------------------


class TestSambaProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        p = _make_samba_provisioner(enabled=False)
        result = p.provision("cust-uuid-2", "sa-2", {})
        assert result.startswith("samba_stub_")

    def test_suspend_is_noop(self):
        p = _make_samba_provisioner(enabled=False)
        p.suspend("ext-2", "cust-2")

    def test_reactivate_is_noop(self):
        p = _make_samba_provisioner(enabled=False)
        p.reactivate("ext-2", "cust-2")

    def test_deprovision_is_noop(self):
        p = _make_samba_provisioner(enabled=False)
        p.deprovision("ext-2", "cust-2")


# ---------------------------------------------------------------------------
# SambaProvisioner — enabled
# ---------------------------------------------------------------------------


class TestSambaProvisionerEnabled:
    def test_provision_returns_prefixed_id(self):
        p = _make_samba_provisioner(enabled=True)
        result = p.provision("cust-uuid-2", "sa-2", {})
        assert result.startswith("samba_")

    def test_suspend_logs_without_raising(self):
        p = _make_samba_provisioner(enabled=True)
        p.suspend("ext-2", "cust-2")

    def test_reactivate_logs_without_raising(self):
        p = _make_samba_provisioner(enabled=True)
        p.reactivate("ext-2", "cust-2")

    def test_deprovision_logs_without_raising(self):
        p = _make_samba_provisioner(enabled=True)
        p.deprovision("ext-2", "cust-2")


# ---------------------------------------------------------------------------
# registry — Samba is registered
# ---------------------------------------------------------------------------


class TestSambaRegistry:
    def test_get_provisioner_returns_samba(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("samba")
        assert provisioner is not None
        assert provisioner.service_key == "samba"


# ---------------------------------------------------------------------------
# Helpers — Plone, TwentyCRM, Papermark, CrowdSec (stub provisioners)
# ---------------------------------------------------------------------------


def _make_stub_provisioner(cls, enabled=False):
    p = cls.__new__(cls)
    p._api_url = "https://example.com" if enabled else ""
    p._api_key = "secret" if enabled else ""
    p._enabled = enabled
    return p


# ---------------------------------------------------------------------------
# PloneProvisioner
# ---------------------------------------------------------------------------


class TestPloneProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        from apps.provisioning.plone import PloneProvisioner

        p = _make_stub_provisioner(PloneProvisioner, enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("plone_stub_")

    def test_suspend_is_noop(self):
        from apps.provisioning.plone import PloneProvisioner

        p = _make_stub_provisioner(PloneProvisioner, enabled=False)
        p.suspend("ext-1", "cust-1")

    def test_reactivate_is_noop(self):
        from apps.provisioning.plone import PloneProvisioner

        p = _make_stub_provisioner(PloneProvisioner, enabled=False)
        p.reactivate("ext-1", "cust-1")

    def test_deprovision_is_noop(self):
        from apps.provisioning.plone import PloneProvisioner

        p = _make_stub_provisioner(PloneProvisioner, enabled=False)
        p.deprovision("ext-1", "cust-1")


class TestPloneProvisionerEnabled:
    def test_provision_returns_prefixed_customer_id(self):
        from apps.provisioning.plone import PloneProvisioner

        p = _make_stub_provisioner(PloneProvisioner, enabled=True)
        result = p.provision("cust-uuid-1", "sa-1", {})
        assert result.startswith("plone_")

    def test_lifecycle_does_not_raise(self):
        from apps.provisioning.plone import PloneProvisioner

        p = _make_stub_provisioner(PloneProvisioner, enabled=True)
        ext_id = p.provision("cust-uuid-1", "sa-1", {})
        p.suspend(ext_id, "cust-uuid-1")
        p.reactivate(ext_id, "cust-uuid-1")
        p.deprovision(ext_id, "cust-uuid-1")


class TestPloneRegistry:
    def test_get_provisioner_returns_plone(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("plone")
        assert provisioner is not None
        assert provisioner.service_key == "plone"


# ---------------------------------------------------------------------------
# TwentyCRMProvisioner
# ---------------------------------------------------------------------------


class TestTwentyCRMProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        from apps.provisioning.twenty_crm import TwentyCRMProvisioner

        p = _make_stub_provisioner(TwentyCRMProvisioner, enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("twenty_stub_")

    def test_lifecycle_noop(self):
        from apps.provisioning.twenty_crm import TwentyCRMProvisioner

        p = _make_stub_provisioner(TwentyCRMProvisioner, enabled=False)
        p.suspend("ext-1", "cust-1")
        p.reactivate("ext-1", "cust-1")
        p.deprovision("ext-1", "cust-1")


class TestTwentyCRMProvisionerEnabled:
    def test_provision_returns_prefixed_customer_id(self):
        from apps.provisioning.twenty_crm import TwentyCRMProvisioner

        p = _make_stub_provisioner(TwentyCRMProvisioner, enabled=True)
        result = p.provision("cust-uuid-2", "sa-2", {})
        assert result.startswith("twenty_")

    def test_lifecycle_does_not_raise(self):
        from apps.provisioning.twenty_crm import TwentyCRMProvisioner

        p = _make_stub_provisioner(TwentyCRMProvisioner, enabled=True)
        ext_id = p.provision("cust-uuid-2", "sa-2", {})
        p.suspend(ext_id, "cust-uuid-2")
        p.reactivate(ext_id, "cust-uuid-2")
        p.deprovision(ext_id, "cust-uuid-2")


class TestTwentyCRMRegistry:
    def test_get_provisioner_returns_twenty_crm(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("twenty_crm")
        assert provisioner is not None
        assert provisioner.service_key == "twenty_crm"


# ---------------------------------------------------------------------------
# PapermarkProvisioner
# ---------------------------------------------------------------------------


class TestPapermarkProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        from apps.provisioning.papermark import PapermarkProvisioner

        p = _make_stub_provisioner(PapermarkProvisioner, enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("papermark_stub_")

    def test_lifecycle_noop(self):
        from apps.provisioning.papermark import PapermarkProvisioner

        p = _make_stub_provisioner(PapermarkProvisioner, enabled=False)
        p.suspend("ext-1", "cust-1")
        p.reactivate("ext-1", "cust-1")
        p.deprovision("ext-1", "cust-1")


class TestPapermarkProvisionerEnabled:
    def test_provision_returns_prefixed_customer_id(self):
        from apps.provisioning.papermark import PapermarkProvisioner

        p = _make_stub_provisioner(PapermarkProvisioner, enabled=True)
        result = p.provision("cust-uuid-3", "sa-3", {})
        assert result.startswith("papermark_")

    def test_lifecycle_does_not_raise(self):
        from apps.provisioning.papermark import PapermarkProvisioner

        p = _make_stub_provisioner(PapermarkProvisioner, enabled=True)
        ext_id = p.provision("cust-uuid-3", "sa-3", {})
        p.suspend(ext_id, "cust-uuid-3")
        p.reactivate(ext_id, "cust-uuid-3")
        p.deprovision(ext_id, "cust-uuid-3")


class TestPapermarkRegistry:
    def test_get_provisioner_returns_papermark(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("papermark")
        assert provisioner is not None
        assert provisioner.service_key == "papermark"


# ---------------------------------------------------------------------------
# CrowdSecProvisioner
# ---------------------------------------------------------------------------


class TestCrowdSecProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        from apps.provisioning.crowdsec import CrowdSecProvisioner

        p = _make_stub_provisioner(CrowdSecProvisioner, enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("crowdsec_stub_")

    def test_lifecycle_noop(self):
        from apps.provisioning.crowdsec import CrowdSecProvisioner

        p = _make_stub_provisioner(CrowdSecProvisioner, enabled=False)
        p.suspend("ext-1", "cust-1")
        p.reactivate("ext-1", "cust-1")
        p.deprovision("ext-1", "cust-1")


class TestCrowdSecProvisionerEnabled:
    def test_provision_returns_prefixed_customer_id(self):
        from apps.provisioning.crowdsec import CrowdSecProvisioner

        p = _make_stub_provisioner(CrowdSecProvisioner, enabled=True)
        result = p.provision("cust-uuid-4", "sa-4", {})
        assert result.startswith("crowdsec_")

    def test_lifecycle_does_not_raise(self):
        from apps.provisioning.crowdsec import CrowdSecProvisioner

        p = _make_stub_provisioner(CrowdSecProvisioner, enabled=True)
        ext_id = p.provision("cust-uuid-4", "sa-4", {})
        p.suspend(ext_id, "cust-uuid-4")
        p.reactivate(ext_id, "cust-uuid-4")
        p.deprovision(ext_id, "cust-uuid-4")


class TestCrowdSecRegistry:
    def test_get_provisioner_returns_crowdsec(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("crowdsec")
        assert provisioner is not None
        assert provisioner.service_key == "crowdsec"


# ---------------------------------------------------------------------------
# KeycloakProvisioner — disabled paths (no credentials)
# ---------------------------------------------------------------------------


def _make_keycloak_provisioner(enabled=False):
    from apps.provisioning.keycloak import KeycloakProvisioner

    p = KeycloakProvisioner.__new__(KeycloakProvisioner)
    p._api_url = "https://keycloak.example.com" if enabled else ""
    p._admin_token = "admin-tok" if enabled else ""
    p._enabled = enabled
    if enabled:
        mock_session = MagicMock()
        p._session = mock_session
        return p, mock_session
    return p, None


class TestKeycloakProvisionerDisabled:
    def test_provision_returns_stub_id(self):
        p, _ = _make_keycloak_provisioner(enabled=False)
        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("keycloak_stub_")

    def test_suspend_is_noop(self):
        p, _ = _make_keycloak_provisioner(enabled=False)
        p.suspend("realm-1", "cust-1")

    def test_reactivate_is_noop(self):
        p, _ = _make_keycloak_provisioner(enabled=False)
        p.reactivate("realm-1", "cust-1")

    def test_deprovision_is_noop(self):
        p, _ = _make_keycloak_provisioner(enabled=False)
        p.deprovision("realm-1", "cust-1")


class TestKeycloakProvisionerEnabled:
    def test_provision_creates_realm_and_returns_realm_name(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.raise_for_status.return_value = None
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-123", "sa-1", {"realm_name": "tenant-abc"})
        assert result == "tenant-abc"
        mock_session.post.assert_called_once()
        assert "/admin/realms" in mock_session.post.call_args[0][0]

    def test_provision_uses_default_realm_name_when_not_in_config(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.raise_for_status.return_value = None
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("tenant-")

    def test_provision_handles_409_realm_already_exists(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 409
        mock_session.post.return_value = mock_resp

        result = p.provision("cust-123", "sa-1", {"realm_name": "existing-realm"})
        assert result == "existing-realm"
        mock_resp.raise_for_status.assert_not_called()

    def test_suspend_disables_realm(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.put.return_value = mock_resp

        p.suspend("realm-xyz", "cust-1")
        mock_session.put.assert_called_once()
        payload = mock_session.put.call_args[1]["json"]
        assert payload["enabled"] is False
        assert "realm-xyz" in mock_session.put.call_args[0][0]

    def test_reactivate_enables_realm(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.put.return_value = mock_resp

        p.reactivate("realm-xyz", "cust-1")
        payload = mock_session.put.call_args[1]["json"]
        assert payload["enabled"] is True

    def test_deprovision_deletes_realm(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.delete.return_value = mock_resp

        p.deprovision("realm-xyz", "cust-1")
        mock_session.delete.assert_called_once()
        assert "realm-xyz" in mock_session.delete.call_args[0][0]

    def test_suspend_ignores_404(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.put.return_value = mock_resp
        p.suspend("realm-xyz", "cust-1")  # should not raise

    def test_deprovision_ignores_404(self):
        p, mock_session = _make_keycloak_provisioner(enabled=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_session.delete.return_value = mock_resp
        p.deprovision("realm-xyz", "cust-1")  # should not raise


class TestKeycloakRegistry:
    def test_get_provisioner_returns_keycloak(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("keycloak")
        assert provisioner is not None
        assert provisioner.service_key == "keycloak"


class TestTailscaleProvisioner:
    def test_provision_returns_stub_id(self):
        from apps.provisioning.tailscale import TailscaleProvisioner

        provisioner = TailscaleProvisioner()
        result = provisioner.provision("cust-abcdefgh", "sa-1", {})
        assert result.startswith("tailscale_stub_")

    def test_lifecycle_methods_do_not_raise(self):
        from apps.provisioning.tailscale import TailscaleProvisioner

        provisioner = TailscaleProvisioner()
        ext_id = provisioner.provision("cust-abcdefgh", "sa-1", {})
        provisioner.suspend(ext_id, "cust-abcdefgh")
        provisioner.reactivate(ext_id, "cust-abcdefgh")
        provisioner.deprovision(ext_id, "cust-abcdefgh")


class TestTailscaleRegistry:
    def test_get_provisioner_returns_tailscale(self):
        from apps.provisioning import registry

        registry._REGISTRY = {}
        provisioner = registry.get_provisioner("tailscale")
        assert provisioner is not None
        assert provisioner.service_key == "tailscale"
