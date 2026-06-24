import logging

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class KeycloakProvisioner(AbstractProvisioner):
    """
    Provisions a Keycloak realm for a customer.

    Uses the Keycloak Admin REST API (POST /admin/realms) to create an isolated
    realm per tenant. Requires KEYCLOAK_API_URL (base URL, e.g. https://auth.papermoon.com)
    and KEYCLOAK_ADMIN_TOKEN (or KEYCLOAK_ADMIN_USER + KEYCLOAK_ADMIN_PASSWORD).

    Falls back to log-only stub when credentials are absent.
    """

    service_key = "keycloak"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "KEYCLOAK_API_URL", "") or "").rstrip("/")
        self._admin_token = getattr(settings, "KEYCLOAK_ADMIN_TOKEN", "") or ""
        self._enabled = bool(self._api_url and self._admin_token)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self._admin_token}",
                    "Content-Type": "application/json",
                }
            )

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "KeycloakProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"keycloak_stub_{customer_id[:8]}"

        realm_name = config.get("realm_name", f"tenant-{customer_id[:8]}")
        resp = self._session.post(
            f"{self._api_url}/admin/realms",
            json={
                "realm": realm_name,
                "enabled": True,
                "displayName": config.get("display_name", realm_name),
            },
        )
        if resp.status_code == 409:
            logger.info("KeycloakProvisioner: realm %s already exists", realm_name)
        else:
            resp.raise_for_status()

        logger.info(
            "KeycloakProvisioner.provision ok customer_id=%s realm=%s",
            customer_id,
            realm_name,
        )
        return realm_name

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "KeycloakProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return

        resp = self._session.put(
            f"{self._api_url}/admin/realms/{external_id}",
            json={"enabled": False},
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("KeycloakProvisioner.suspend ok realm=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "KeycloakProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return

        resp = self._session.put(
            f"{self._api_url}/admin/realms/{external_id}",
            json={"enabled": True},
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("KeycloakProvisioner.reactivate ok realm=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "KeycloakProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return

        resp = self._session.delete(f"{self._api_url}/admin/realms/{external_id}")
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("KeycloakProvisioner.deprovision ok realm=%s", external_id)
