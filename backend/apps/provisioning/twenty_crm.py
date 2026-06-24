import logging

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class TwentyCRMProvisioner(AbstractProvisioner):
    """
    Provisioner for self-hosted Twenty CRM instances.

    Twenty CRM is deployed as a dedicated Docker Compose stack per customer.
    The project does not yet expose a stable tenant-management API. Until then,
    all lifecycle operations log the required manual action and return a stub ID
    so the ServiceAccess record is created correctly.
    """

    service_key = "twenty_crm"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "TWENTY_CRM_API_URL", "") or "").rstrip("/")
        self._api_key = getattr(settings, "TWENTY_CRM_API_KEY", "") or ""
        self._enabled = bool(self._api_url and self._api_key)

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "TwentyCRMProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"twenty_stub_{customer_id[:8]}"

        logger.info(
            "TwentyCRMProvisioner.provision called customer_id=%s config=%s",
            customer_id,
            config,
        )
        return f"twenty_{customer_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "TwentyCRMProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("TwentyCRMProvisioner.suspend called external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "TwentyCRMProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("TwentyCRMProvisioner.reactivate called external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "TwentyCRMProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("TwentyCRMProvisioner.deprovision called external_id=%s", external_id)
