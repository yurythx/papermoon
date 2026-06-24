import logging

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class RustDeskProvisioner(AbstractProvisioner):
    """
    Provisions customer access in a self-hosted RustDesk Server Pro instance.

    Requires RUSTDESK_API_URL and RUSTDESK_API_KEY in settings.
    Falls back to a log-only stub when credentials are absent (the open-source
    community server has no management API — setup is manual in that case).

    RustDesk Server Pro API:
    https://rustdesk.com/docs/en/self-host/rustdesk-server-pro/api/
    Flow: create user (POST /api/user) → return guid
    """

    service_key = "rustdesk"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "RUSTDESK_API_URL", "") or "").rstrip("/")
        self._api_key = getattr(settings, "RUSTDESK_API_KEY", "") or ""
        self._enabled = bool(self._api_url and self._api_key)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }
            )

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "RustDeskProvisioner.provision skipped — credentials not set customer_id=%s",
                customer_id,
            )
            return f"rustdesk_stub_{customer_id[:8]}"

        name = config.get("name", f"PaperMoon {customer_id[:8]}")
        email = config.get("admin_email", f"rustdesk_{customer_id[:8]}@tenants.papermoon.com")
        password = config.get("password") or self._generate_password()

        resp = self._session.post(
            f"{self._api_url}/api/user",
            json={
                "name": name,
                "email": email,
                "password": password,
                "confirm_password": password,
                "status": 1,  # 1=active
                "role": "regular",
                "is_admin": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        # Server Pro returns "guid"; fall back to "id" for future compatibility
        user_id = str(data.get("guid") or data.get("id") or customer_id[:8])
        logger.info(
            "RustDeskProvisioner.provision ok customer_id=%s rustdesk_user_id=%s",
            customer_id,
            user_id,
        )
        return user_id

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("RustDeskProvisioner.suspend skipped — credentials not set")
            return

        resp = self._session.put(
            f"{self._api_url}/api/user/{external_id}",
            json={"status": 2},  # 2=disabled in Server Pro
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("RustDeskProvisioner.suspend ok external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("RustDeskProvisioner.reactivate skipped — credentials not set")
            return

        resp = self._session.put(
            f"{self._api_url}/api/user/{external_id}",
            json={"status": 1},  # 1=active
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("RustDeskProvisioner.reactivate ok external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("RustDeskProvisioner.deprovision skipped — credentials not set")
            return

        resp = self._session.delete(f"{self._api_url}/api/user/{external_id}")
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("RustDeskProvisioner.deprovision ok external_id=%s", external_id)

    # ------------------------------------------------------------------

    @staticmethod
    def _generate_password() -> str:
        import secrets

        return secrets.token_urlsafe(16)
