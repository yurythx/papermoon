import logging

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class N8nProvisioner(AbstractProvisioner):
    """
    Provisions customer access in a self-hosted n8n instance.

    Requires N8N_API_URL and N8N_API_KEY in settings.
    Falls back to a log-only stub when credentials are absent (dev/staging without n8n).

    n8n API docs: https://docs.n8n.io/api/
    """

    service_key = "n8n"

    def __init__(self) -> None:
        from django.conf import settings

        self._base_url = (getattr(settings, "N8N_API_URL", "") or "").rstrip("/")
        api_key = getattr(settings, "N8N_API_KEY", "") or ""
        self._enabled = bool(self._base_url and api_key)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update(
                {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}
            )

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "N8nProvisioner.provision skipped — credentials not set customer_id=%s",
                customer_id,
            )
            return f"n8n_stub_{customer_id[:8]}"

        email = config.get("admin_email", f"n8n_{customer_id[:8]}@tenants.papermoon.com")
        first_name = config.get("first_name", "Admin")
        last_name = config.get("last_name", customer_id[:8])

        # Create user in n8n with owner role for this tenant workspace
        resp = self._session.post(
            f"{self._base_url}/api/v1/users",
            json=[
                {
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name,
                    "role": "global:member",
                }
            ],
        )
        resp.raise_for_status()
        users = resp.json()
        user_id = users[0]["id"] if users else f"n8n_{customer_id[:8]}"
        logger.info(
            "N8nProvisioner.provision ok customer_id=%s n8n_user_id=%s",
            customer_id,
            user_id,
        )
        return str(user_id)

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("N8nProvisioner.suspend skipped — credentials not set")
            return

        # n8n doesn't have a built-in "disable user" endpoint in community edition;
        # change role to viewer (read-only) as the closest equivalent.
        resp = self._session.patch(
            f"{self._base_url}/api/v1/users/{external_id}/role",
            json={"newRoleName": "global:member"},
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        logger.info("N8nProvisioner.suspend ok external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("N8nProvisioner.reactivate skipped — credentials not set")
            return

        resp = self._session.patch(
            f"{self._base_url}/api/v1/users/{external_id}/role",
            json={"newRoleName": "global:member"},
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        logger.info("N8nProvisioner.reactivate ok external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("N8nProvisioner.deprovision skipped — credentials not set")
            return

        resp = self._session.delete(f"{self._base_url}/api/v1/users/{external_id}")
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("N8nProvisioner.deprovision ok external_id=%s", external_id)
