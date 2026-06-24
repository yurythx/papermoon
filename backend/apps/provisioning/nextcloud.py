from apps.provisioning.base import AbstractProvisioner


class NextcloudProvisioner(AbstractProvisioner):
    """
    Implantação de Nextcloud — processo manual executado pela equipe PaperMoon.
    O external_id é preenchido pelo admin com a URL do servidor após instalação.
    """

    service_key = "nextcloud"

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        return f"nextcloud-pending-{service_access_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        pass

    def reactivate(self, external_id: str, customer_id: str) -> None:
        pass

    def deprovision(self, external_id: str, customer_id: str) -> None:
        pass
