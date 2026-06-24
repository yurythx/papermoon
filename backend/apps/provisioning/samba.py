import logging

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class SambaProvisioner(AbstractProvisioner):
    """
    Provisioner for Linux Samba file-server environments.

    Samba ships no standard REST management API. Administration is done via
    smbpasswd / net commands over SSH, or through optional management tools
    (Cockpit + samba extension, Zentyal, etc.). When a management API URL is
    configured (SAMBA_API_URL + SAMBA_API_KEY), future automation can hook here.
    Until then, every call logs the required action and returns a stub ID so the
    ServiceAccess record is created correctly.
    """

    service_key = "samba"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "SAMBA_API_URL", "") or "").rstrip("/")
        self._api_key = getattr(settings, "SAMBA_API_KEY", "") or ""
        self._enabled = bool(self._api_url and self._api_key)

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "SambaProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"samba_stub_{customer_id[:8]}"

        logger.info(
            "SambaProvisioner.provision called customer_id=%s config=%s",
            customer_id,
            config,
        )
        return f"samba_{customer_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "SambaProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return

        logger.info("SambaProvisioner.suspend called external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "SambaProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return

        logger.info("SambaProvisioner.reactivate called external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "SambaProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return

        logger.info("SambaProvisioner.deprovision called external_id=%s", external_id)
