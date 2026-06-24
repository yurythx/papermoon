from apps.provisioning.base import AbstractProvisioner


class AAPanelProvisioner(AbstractProvisioner):
    """
    Implantação de AAPanel — processo manual executado pela equipe PaperMoon.
    O external_id é preenchido pelo admin com a URL do painel após instalação.
    """

    service_key = "aapanel"

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        return f"aapanel-pending-{service_access_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        pass

    def reactivate(self, external_id: str, customer_id: str) -> None:
        pass

    def deprovision(self, external_id: str, customer_id: str) -> None:
        pass
