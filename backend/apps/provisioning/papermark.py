import logging

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class PapermarkProvisioner(AbstractProvisioner):
    """
    Provisioner for self-hosted Papermark instances.

    Papermark is deployed as a single-tenant Docker Compose stack per customer.
    There is no multi-tenant management API in the open-source version. Until
    an automation layer is built, all lifecycle operations log the required
    manual action and return a stub ID so the ServiceAccess record is created.
    """

    service_key = "papermark"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "PAPERMARK_API_URL", "") or "").rstrip("/")
        self._api_key = getattr(settings, "PAPERMARK_API_KEY", "") or ""
        self._enabled = bool(self._api_url and self._api_key)

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "PapermarkProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"papermark_stub_{customer_id[:8]}"

        logger.info(
            "PapermarkProvisioner.provision called customer_id=%s config=%s",
            customer_id,
            config,
        )
        return f"papermark_{customer_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "PapermarkProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("PapermarkProvisioner.suspend called external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "PapermarkProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("PapermarkProvisioner.reactivate called external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "PapermarkProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("PapermarkProvisioner.deprovision called external_id=%s", external_id)
