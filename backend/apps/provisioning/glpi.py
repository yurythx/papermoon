import logging

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class GLPIProvisioner(AbstractProvisioner):
    """
    Provisions customer access in a self-hosted GLPI instance.

    Requires GLPI_API_URL and GLPI_APP_TOKEN in settings.
    Falls back to a log-only stub when credentials are absent.

    GLPI REST API docs: https://github.com/glpi-project/glpi/blob/main/apirest.md
    Flow: init session → create user → add to helpdesk profile → return user_id
    """

    service_key = "glpi"

    def __init__(self) -> None:
        from django.conf import settings

        self._base_url = (getattr(settings, "GLPI_API_URL", "") or "").rstrip("/")
        self._app_token = getattr(settings, "GLPI_APP_TOKEN", "") or ""
        self._user_token = getattr(settings, "GLPI_USER_TOKEN", "") or ""
        self._enabled = bool(self._base_url and self._app_token and self._user_token)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "App-Token": self._app_token,
                    "Content-Type": "application/json",
                }
            )

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "GLPIProvisioner.provision skipped — credentials not set customer_id=%s",
                customer_id,
            )
            return f"glpi_stub_{customer_id[:8]}"

        session_token = self._init_session()
        try:
            name = config.get("name", f"PaperMoon {customer_id[:8]}")
            login = config.get("login", f"papermoon_{customer_id[:8]}")
            email = config.get("admin_email", f"glpi_{customer_id[:8]}@tenants.papermoon.com")
            password = config.get("password", self._generate_password(customer_id))

            resp = self._session.post(
                f"{self._base_url}/apirest.php/User",
                headers={"Session-Token": session_token},
                json={
                    "input": {
                        "name": login,
                        "realname": name,
                        "email": email,
                        "password": password,
                        "password2": password,
                        "is_active": 1,
                        "profiles_id": config.get("profile_id", 4),  # default: Technician
                    }
                },
            )
            resp.raise_for_status()
            user_id = resp.json().get("id", f"glpi_{customer_id[:8]}")
            logger.info(
                "GLPIProvisioner.provision ok customer_id=%s glpi_user_id=%s",
                customer_id,
                user_id,
            )
            return str(user_id)
        finally:
            self._kill_session(session_token)

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("GLPIProvisioner.suspend skipped — credentials not set")
            return

        session_token = self._init_session()
        try:
            resp = self._session.put(
                f"{self._base_url}/apirest.php/User/{external_id}",
                headers={"Session-Token": session_token},
                json={"input": {"is_active": 0}},
            )
            if resp.status_code not in (200, 201, 404):
                resp.raise_for_status()
        finally:
            self._kill_session(session_token)
        logger.info("GLPIProvisioner.suspend ok external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("GLPIProvisioner.reactivate skipped — credentials not set")
            return

        session_token = self._init_session()
        try:
            resp = self._session.put(
                f"{self._base_url}/apirest.php/User/{external_id}",
                headers={"Session-Token": session_token},
                json={"input": {"is_active": 1}},
            )
            if resp.status_code not in (200, 201, 404):
                resp.raise_for_status()
        finally:
            self._kill_session(session_token)
        logger.info("GLPIProvisioner.reactivate ok external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("GLPIProvisioner.deprovision skipped — credentials not set")
            return

        session_token = self._init_session()
        try:
            resp = self._session.delete(
                f"{self._base_url}/apirest.php/User/{external_id}",
                headers={"Session-Token": session_token},
            )
            if resp.status_code not in (200, 204, 404):
                resp.raise_for_status()
        finally:
            self._kill_session(session_token)
        logger.info("GLPIProvisioner.deprovision ok external_id=%s", external_id)

    # ------------------------------------------------------------------

    def _init_session(self) -> str:
        resp = self._session.get(
            f"{self._base_url}/apirest.php/initSession",
            headers={"Authorization": f"user_token {self._user_token}"},
        )
        resp.raise_for_status()
        return resp.json()["session_token"]

    def _kill_session(self, session_token: str) -> None:
        import contextlib

        with contextlib.suppress(Exception):
            self._session.get(
                f"{self._base_url}/apirest.php/killSession",
                headers={"Session-Token": session_token},
            )

    @staticmethod
    def _generate_password(customer_id: str) -> str:
        import secrets

        return secrets.token_urlsafe(16)
