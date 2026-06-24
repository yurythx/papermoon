import logging

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class TailscaleProvisioner(AbstractProvisioner):
    """
    Manual-first provisioner for Tailscale deployments.

    Tailscale onboarding usually depends on customer identity provider setup,
    ACL review, subnet router planning and device enrollment. Until the
    automation path is defined, the internal provisioning flow uses a safe
    log-only stub so the service can be sold and tracked without becoming an
    "unknown service_key".
    """

    service_key = "tailscale"

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        logger.warning(
            "TailscaleProvisioner.provision — manual setup required customer_id=%s service_access_id=%s",
            customer_id,
            service_access_id,
        )
        return f"tailscale_stub_{customer_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        logger.warning(
            "TailscaleProvisioner.suspend — manual action required external_id=%s customer_id=%s",
            external_id,
            customer_id,
        )

    def reactivate(self, external_id: str, customer_id: str) -> None:
        logger.warning(
            "TailscaleProvisioner.reactivate — manual action required external_id=%s customer_id=%s",
            external_id,
            customer_id,
        )

    def deprovision(self, external_id: str, customer_id: str) -> None:
        logger.warning(
            "TailscaleProvisioner.deprovision — manual action required external_id=%s customer_id=%s",
            external_id,
            customer_id,
        )
