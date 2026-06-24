from apps.provisioning.base import AbstractProvisioner


class EvolutionApiProvisioner(AbstractProvisioner):
    """
    Implantação de Evolution API — processo manual executado pela equipe PaperMoon.
    Inclui configuração de webhook, integração com n8n/Chatwoot e treinamento.
    O external_id é preenchido com a URL da instância após instalação.

    IMPORTANTE: Evolution API usa o protocolo WhatsApp Web (não oficial).
    Risco de ban da conta existe; recomendar apenas para uso interno/baixo volume.
    """

    service_key = "evolution_api"

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        return f"evolution-pending-{service_access_id[:8]}"

    def suspend(self, external_id: str, customer_id: str) -> None:
        pass

    def reactivate(self, external_id: str, customer_id: str) -> None:
        pass

    def deprovision(self, external_id: str, customer_id: str) -> None:
        pass
