from apps.provisioning.base import AbstractProvisioner

_REGISTRY: dict[str, AbstractProvisioner] = {}


def _build() -> dict[str, AbstractProvisioner]:
    from apps.provisioning.aapanel import AAPanelProvisioner
    from apps.provisioning.chatwoot import ChatwootProvisioner
    from apps.provisioning.crowdsec import CrowdSecProvisioner
    from apps.provisioning.evolution_api import EvolutionApiProvisioner
    from apps.provisioning.glpi import GLPIProvisioner
    from apps.provisioning.keycloak import KeycloakProvisioner
    from apps.provisioning.meta_api import MetaWhatsAppProvisioner
    from apps.provisioning.n8n import N8nProvisioner
    from apps.provisioning.nextcloud import NextcloudProvisioner
    from apps.provisioning.papermark import PapermarkProvisioner
    from apps.provisioning.plone import PloneProvisioner
    from apps.provisioning.proxmox import ProxmoxProvisioner
    from apps.provisioning.rustdesk import RustDeskProvisioner
    from apps.provisioning.samba import SambaProvisioner
    from apps.provisioning.tailscale import TailscaleProvisioner
    from apps.provisioning.truenas import TrueNASProvisioner
    from apps.provisioning.twenty_crm import TwentyCRMProvisioner
    from apps.provisioning.windows_server import WindowsServerProvisioner
    from apps.provisioning.zabbix import ZabbixProvisioner

    provisioners: list[AbstractProvisioner] = [
        ChatwootProvisioner(),
        MetaWhatsAppProvisioner(),
        N8nProvisioner(),
        GLPIProvisioner(),
        ZabbixProvisioner(),
        ProxmoxProvisioner(),
        TrueNASProvisioner(),
        NextcloudProvisioner(),
        AAPanelProvisioner(),
        EvolutionApiProvisioner(),
        RustDeskProvisioner(),
        WindowsServerProvisioner(),
        SambaProvisioner(),
        PloneProvisioner(),
        KeycloakProvisioner(),
        TailscaleProvisioner(),
        TwentyCRMProvisioner(),
        PapermarkProvisioner(),
        CrowdSecProvisioner(),
    ]
    return {p.service_key: p for p in provisioners}


def get_provisioner(service_key: str) -> AbstractProvisioner | None:
    global _REGISTRY
    if not _REGISTRY:
        _REGISTRY = _build()
    return _REGISTRY.get(service_key)
