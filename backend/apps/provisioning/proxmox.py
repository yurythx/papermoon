from apps.provisioning.base import AbstractProvisioner


class ProxmoxProvisioner(AbstractProvisioner):
    """
    Implantação de Proxmox VE — processo manual executado pela equipe PaperMoon.
    O provisioner registra a solicitação; o external_id é preenchido pelo admin
    após a instalação física no servidor do cliente.
    """

    service_key = "proxmox"

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        # Implantação manual — retorna um ticket de solicitação como external_id
        return f"proxmox-pending-{service_access_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        # Suspensão de serviço implantado é comunicada manualmente ao cliente
        pass

    def reactivate(self, external_id: str, customer_id: str) -> None:
        pass

    def deprovision(self, external_id: str, customer_id: str) -> None:
        pass
