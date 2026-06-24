import logging

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class WindowsServerProvisioner(AbstractProvisioner):
    """
    Provisioner for Windows Server environments (Active Directory + File Server).

    Windows Server management has no standard public REST API — configuration is
    performed via WinRM/PowerShell or Windows Admin Center (WAC). When WAC
    credentials are provided (WINDOWS_SERVER_WAC_URL + WINDOWS_SERVER_WAC_KEY),
    future automation can hook here. Until then, every call logs the required
    action and returns a stub ID so the ServiceAccess record is created.
    """

    service_key = "windows-server"

    def __init__(self) -> None:
        from django.conf import settings

        self._wac_url = (getattr(settings, "WINDOWS_SERVER_WAC_URL", "") or "").rstrip("/")
        self._wac_key = getattr(settings, "WINDOWS_SERVER_WAC_KEY", "") or ""
        self._enabled = bool(self._wac_url and self._wac_key)

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "WindowsServerProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"winserver_stub_{customer_id[:8]}"

        # Placeholder for WAC automation when REST endpoint is available.
        logger.info(
            "WindowsServerProvisioner.provision called customer_id=%s config=%s",
            customer_id,
            config,
        )
        return f"winserver_{customer_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "WindowsServerProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return

        logger.info("WindowsServerProvisioner.suspend called external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "WindowsServerProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return

        logger.info("WindowsServerProvisioner.reactivate called external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning(
                "WindowsServerProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return

        logger.info("WindowsServerProvisioner.deprovision called external_id=%s", external_id)
