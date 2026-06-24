import logging

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class PloneProvisioner(AbstractProvisioner):
    """
    Provisioner for self-hosted Plone CMS instances.

    Plone does not expose a standard REST management API for tenant provisioning.
    Each deployment is a dedicated instance per customer. Until a management
    layer is built (Plone REST API + custom scripts), all lifecycle operations
    log the required manual action and return a stub ID so the ServiceAccess
    record is created correctly.
    """

    service_key = "plone"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "PLONE_API_URL", "") or "").rstrip("/")
        self._api_key = getattr(settings, "PLONE_API_KEY", "") or ""
        self._enabled = bool(self._api_url and self._api_key)

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "PloneProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"plone_stub_{customer_id[:8]}"

        logger.info(
            "PloneProvisioner.provision called customer_id=%s config=%s",
            customer_id,
            config,
        )
        return f"plone_{customer_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "PloneProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("PloneProvisioner.suspend called external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "PloneProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("PloneProvisioner.reactivate called external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "PloneProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return
        logger.info("PloneProvisioner.deprovision called external_id=%s", external_id)
