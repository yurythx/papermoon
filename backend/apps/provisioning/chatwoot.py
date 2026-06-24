import logging

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class ChatwootProvisioner(AbstractProvisioner):
    """
    Provisions customer workspace in Chatwoot.

    Requires CHATWOOT_API_URL and CHATWOOT_API_KEY in settings.
    Falls back to a log-only stub when credentials are absent (dev/staging without Chatwoot).
    """

    service_key = "chatwoot"

    def __init__(self) -> None:
        from django.conf import settings

        url = getattr(settings, "CHATWOOT_API_URL", "") or ""
        key = getattr(settings, "CHATWOOT_API_KEY", "") or ""
        self._enabled = bool(url and key)
        if self._enabled:
            from apps.support.client import ChatwootClient

            self._client = ChatwootClient()

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "ChatwootProvisioner.provision skipped — credentials not set customer_id=%s",
                customer_id,
            )
            return f"chatwoot_stub_{customer_id[:8]}"

        data = self._client.provision_customer(customer_id)
        external_id = str(data.get("id", customer_id))
        logger.info(
            "ChatwootProvisioner.provision ok customer_id=%s external_id=%s",
            customer_id,
            external_id,
        )
        return external_id

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("ChatwootProvisioner.suspend skipped — credentials not set")
            return

        self._client.suspend_agents(customer_id)
        logger.info("ChatwootProvisioner.suspend ok customer_id=%s", customer_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("ChatwootProvisioner.reactivate skipped — credentials not set")
            return

        self._client.reactivate_agents(customer_id)
        logger.info("ChatwootProvisioner.reactivate ok customer_id=%s", customer_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("ChatwootProvisioner.deprovision skipped — credentials not set")
            return

        # Chatwoot doesn't expose a delete endpoint — suspend is the safe fallback
        self._client.suspend_agents(customer_id)
        logger.info("ChatwootProvisioner.deprovision ok customer_id=%s", customer_id)
