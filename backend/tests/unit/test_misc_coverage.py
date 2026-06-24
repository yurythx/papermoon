"""
Targeted unit tests for modules with low coverage:
- shared/tasks.py (cleanup_old_outbox_events)
- shared/exceptions.py (custom_exception_handler)
- apps/accounts/serializers.py (UserSerializer)
- apps/support/client.py (ChatwootClient)
- apps/support/commands.py (Provision/Suspend/ReactivateAccessCommand)
- apps/provisioning/chatwoot.py (ChatwootProvisioner)
- apps/provisioning/registry.py (get_provisioner)
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

# ---------------------------------------------------------------------------
# shared/tasks.py — cleanup_old_outbox_events
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCleanupOldOutboxEvents:
    def _create_processed_event(self, processed_at):
        from shared.models import OutboxEvent

        return OutboxEvent.objects.create(
            event_type="test.event",
            payload={},
            processed=True,
            processed_at=processed_at,
        )

    def test_deletes_events_older_than_30_days(self):
        from django.utils import timezone

        from shared.tasks import cleanup_old_outbox_events

        old_time = timezone.now() - datetime.timedelta(days=31)
        event = self._create_processed_event(old_time)

        cleanup_old_outbox_events()

        from shared.models import OutboxEvent

        assert not OutboxEvent.objects.filter(id=event.id).exists()

    def test_keeps_events_within_30_days(self):
        from django.utils import timezone

        from shared.tasks import cleanup_old_outbox_events

        recent_time = timezone.now() - datetime.timedelta(days=29)
        event = self._create_processed_event(recent_time)

        cleanup_old_outbox_events()

        from shared.models import OutboxEvent

        assert OutboxEvent.objects.filter(id=event.id).exists()

    def test_keeps_unprocessed_events(self):
        from shared.models import OutboxEvent
        from shared.tasks import cleanup_old_outbox_events

        event = OutboxEvent.objects.create(
            event_type="test.event",
            payload={},
            processed=False,
        )

        cleanup_old_outbox_events()

        assert OutboxEvent.objects.filter(id=event.id).exists()


# ---------------------------------------------------------------------------
# shared/exceptions.py — custom_exception_handler
# ---------------------------------------------------------------------------


class TestCustomExceptionHandler:
    def _make_context(self):
        return {"request": MagicMock()}

    def test_subscription_suspended_error_returns_403(self):
        from shared.exceptions import SubscriptionSuspendedError, custom_exception_handler

        exc = SubscriptionSuspendedError("suspended")
        resp = custom_exception_handler(exc, self._make_context())
        assert resp.status_code == 403
        assert resp.data["code"] == "subscription_suspended"

    def test_returns_none_for_unhandled_exceptions(self):
        from shared.exceptions import custom_exception_handler

        resp = custom_exception_handler(RuntimeError("boom"), self._make_context())
        assert resp is None

    def test_maps_permission_denied_to_code(self):
        from rest_framework.exceptions import PermissionDenied

        from shared.exceptions import custom_exception_handler

        exc = PermissionDenied("no access")
        resp = custom_exception_handler(exc, self._make_context())
        assert resp is not None
        assert resp.data["code"] == "permission_denied"

    def test_maps_not_found_to_code(self):
        from rest_framework.exceptions import NotFound

        from shared.exceptions import custom_exception_handler

        exc = NotFound("missing")
        resp = custom_exception_handler(exc, self._make_context())
        assert resp is not None
        assert resp.data["code"] == "not_found"

    def test_validation_error_with_list_detail(self):
        from rest_framework.exceptions import ValidationError

        from shared.exceptions import custom_exception_handler

        exc = ValidationError(["field error 1", "field error 2"])
        resp = custom_exception_handler(exc, self._make_context())
        assert resp is not None
        assert resp.data["code"] == "validation_error"
        assert isinstance(resp.data["details"], list)


# ---------------------------------------------------------------------------
# apps/accounts/serializers.py — UserSerializer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserSerializer:
    def test_serializes_user_fields(self):
        from apps.accounts.models import CustomUser
        from apps.accounts.serializers import UserSerializer

        user = CustomUser.objects.create_user(
            username="serialtest",
            email="serialtest@example.com",
            password="x",
            first_name="Test",
            last_name="User",
        )
        data = UserSerializer(user).data
        assert data["email"] == "serialtest@example.com"
        assert data["username"] == "serialtest"
        assert "id" in data
        assert "created_at" in data


# ---------------------------------------------------------------------------
# apps/support/client.py — ChatwootClient
# ---------------------------------------------------------------------------


class TestChatwootClient:
    def _make_client(self):
        with patch("apps.support.client.requests.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            from apps.support.client import ChatwootClient

            with patch("django.conf.settings") as mock_settings:
                mock_settings.CHATWOOT_API_URL = "https://chat.example.com"
                mock_settings.CHATWOOT_API_KEY = "test-key"
                client = ChatwootClient.__new__(ChatwootClient)
                client._base_url = "https://chat.example.com"
                client._session = mock_session
            return client, mock_session

    def test_suspend_agents_success(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_session.post.return_value = mock_resp

        result = client.suspend_agents("cust-123")
        assert result is True
        mock_session.post.assert_called_once()

    def test_suspend_agents_raises_on_request_exception(self):
        client, mock_session = self._make_client()
        mock_session.post.side_effect = requests.RequestException("timeout")

        with pytest.raises(requests.RequestException):
            client.suspend_agents("cust-123")

    def test_reactivate_agents_success(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_session.post.return_value = mock_resp

        result = client.reactivate_agents("cust-456")
        assert result is True

    def test_reactivate_agents_raises_on_request_exception(self):
        client, mock_session = self._make_client()
        mock_session.post.side_effect = requests.RequestException("conn refused")

        with pytest.raises(requests.RequestException):
            client.reactivate_agents("cust-456")

    def test_provision_customer_success(self):
        client, mock_session = self._make_client()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"id": "ws-99"}
        mock_session.post.return_value = mock_resp

        result = client.provision_customer("cust-789")
        assert result == {"id": "ws-99"}

    def test_provision_customer_raises_on_request_exception(self):
        client, mock_session = self._make_client()
        mock_session.post.side_effect = requests.RequestException("network error")

        with pytest.raises(requests.RequestException):
            client.provision_customer("cust-789")


# ---------------------------------------------------------------------------
# apps/support/commands.py
# ---------------------------------------------------------------------------


class TestSupportCommands:
    def test_provision_customer_command_calls_client(self):
        from apps.support.commands import ProvisionCustomerCommand

        with patch("apps.support.commands.ChatwootClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            ProvisionCustomerCommand("cust-1").execute()

            mock_client.provision_customer.assert_called_once_with("cust-1")

    def test_suspend_access_command_calls_client(self):
        from apps.support.commands import SuspendAccessCommand

        with patch("apps.support.commands.ChatwootClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            SuspendAccessCommand("cust-2").execute()

            mock_client.suspend_agents.assert_called_once_with("cust-2")

    def test_reactivate_access_command_calls_client(self):
        from apps.support.commands import ReactivateAccessCommand

        with patch("apps.support.commands.ChatwootClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            ReactivateAccessCommand("cust-3").execute()

            mock_client.reactivate_agents.assert_called_once_with("cust-3")


# ---------------------------------------------------------------------------
# apps/provisioning/chatwoot.py — ChatwootProvisioner
# ---------------------------------------------------------------------------


class TestChatwootProvisioner:
    def _make_provisioner(self):
        from apps.provisioning.chatwoot import ChatwootProvisioner

        p = ChatwootProvisioner.__new__(ChatwootProvisioner)
        p._enabled = True
        p._client = MagicMock()
        return p

    def test_provision_calls_provision_customer(self):
        p = self._make_provisioner()
        p._client.provision_customer.return_value = {"id": "ws-1"}

        result = p.provision("cust-1", "sa-1", {})
        assert result == "ws-1"
        p._client.provision_customer.assert_called_once_with("cust-1")

    def test_suspend_calls_suspend_agents(self):
        p = self._make_provisioner()

        p.suspend("ext-1", "cust-1")
        p._client.suspend_agents.assert_called_once_with("cust-1")

    def test_reactivate_calls_reactivate_agents(self):
        p = self._make_provisioner()

        p.reactivate("ext-1", "cust-1")
        p._client.reactivate_agents.assert_called_once_with("cust-1")

    def test_deprovision_falls_back_to_suspend(self):
        p = self._make_provisioner()

        p.deprovision("ext-1", "cust-1")
        # deprovision calls suspend_agents as fallback (Chatwoot has no delete endpoint)
        p._client.suspend_agents.assert_called_once_with("cust-1")


# ---------------------------------------------------------------------------
# apps/provisioning/registry.py — get_provisioner
# ---------------------------------------------------------------------------


class TestProvisioningRegistry:
    def setup_method(self):
        import apps.provisioning.registry as reg

        reg._REGISTRY = {}

    def test_get_provisioner_returns_n8n(self):
        from apps.provisioning.registry import get_provisioner

        with patch("apps.provisioning.n8n.requests.Session"):
            with patch("django.conf.settings") as ms:
                ms.N8N_API_URL = ""
                ms.N8N_API_KEY = ""
                ms.CHATWOOT_API_URL = "https://c.example.com"
                ms.CHATWOOT_API_KEY = "k"
                ms.META_WHATSAPP_TOKEN = ""
                ms.META_WABA_ID = ""
                from apps.provisioning.n8n import N8nProvisioner

                result = get_provisioner("n8n")
                assert isinstance(result, N8nProvisioner)

    def test_get_provisioner_returns_none_for_unknown_key(self):
        from apps.provisioning.registry import get_provisioner

        with patch("apps.provisioning.n8n.requests.Session"):
            with patch("django.conf.settings") as ms:
                ms.N8N_API_URL = ""
                ms.N8N_API_KEY = ""
                ms.CHATWOOT_API_URL = "https://c.example.com"
                ms.CHATWOOT_API_KEY = "k"
                ms.META_WHATSAPP_TOKEN = ""
                ms.META_WABA_ID = ""
                result = get_provisioner("unknown_service_xyz")
                assert result is None
