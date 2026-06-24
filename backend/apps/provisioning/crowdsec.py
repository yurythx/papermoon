import logging

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class CrowdSecProvisioner(AbstractProvisioner):
    """
    Provisioner for CrowdSec agent deployments.

    CrowdSec is installed as an agent on each customer's server(s). The
    CrowdSec Console API (https://app.crowdsec.net/api) can be used to enroll
    machines and manage blocklists. Requires CROWDSEC_API_URL and
    CROWDSEC_API_KEY (Console API key).

    Falls back to log-only stub when credentials are absent — agent is deployed
    manually by the PaperMoon team via SSH.
    """

    service_key = "crowdsec"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "CROWDSEC_API_URL", "") or "").rstrip("/")
        self._api_key = getattr(settings, "CROWDSEC_API_KEY", "") or ""
        self._enabled = bool(self._api_url and self._api_key)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "x-api-key": self._api_key,
                    "Content-Type": "application/json",
                }
            )

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "CrowdSecProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"crowdsec_stub_{customer_id[:8]}"

        logger.info(
            "CrowdSecProvisioner.provision called customer_id=%s config=%s",
            customer_id,
            config,
        )
        return f"crowdsec_{customer_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "CrowdSecProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("CrowdSecProvisioner.suspend called external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "CrowdSecProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("CrowdSecProvisioner.reactivate called external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "CrowdSecProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("CrowdSecProvisioner.deprovision called external_id=%s", external_id)
