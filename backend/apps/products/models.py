from uuid import uuid4

from django.db import models


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"

    def __str__(self) -> str:
        return self.name


class ServiceComponent(models.Model):
    """Defines which microservices are included in a product."""

    CHATWOOT = "chatwoot"
    META_WHATSAPP = "meta_whatsapp"
    N8N = "n8n"
    GLPI = "glpi"
    ZABBIX = "zabbix"
    PROXMOX = "proxmox"
    TRUENAS = "truenas"
    NEXTCLOUD = "nextcloud"
    AAPANEL = "aapanel"
    EVOLUTION_API = "evolution_api"
    RUSTDESK = "rustdesk"
    SAMBA = "samba"
    WINDOWS_SERVER = "windows-server"
    PLONE = "plone"
    KEYCLOAK = "keycloak"
    TAILSCALE = "tailscale"
    TWENTY_CRM = "twenty_crm"
    PAPERMARK = "papermark"
    CROWDSEC = "crowdsec"

    SERVICE_KEY_CHOICES = [
        (CHATWOOT, "Chatwoot"),
        (META_WHATSAPP, "WhatsApp API Meta"),
        (N8N, "n8n Automação"),
        (GLPI, "GLPI Helpdesk"),
        (ZABBIX, "Zabbix Monitoramento"),
        (PROXMOX, "Proxmox VE"),
        (TRUENAS, "TrueNAS"),
        (NEXTCLOUD, "Nextcloud"),
        (AAPANEL, "AAPanel"),
        (EVOLUTION_API, "Evolution API"),
        (RUSTDESK, "RustDesk"),
        (SAMBA, "Samba File Server"),
        (WINDOWS_SERVER, "Windows Server / AD"),
        (PLONE, "Plone CMS"),
        (KEYCLOAK, "Keycloak IAM/SSO"),
        (TAILSCALE, "Tailscale"),
        (TWENTY_CRM, "Twenty CRM"),
        (PAPERMARK, "Papermark"),
        (CROWDSEC, "CrowdSec"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="components")
    service_key = models.CharField(max_length=50, choices=SERVICE_KEY_CHOICES)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "product_service_components"
        unique_together = [("product", "service_key")]

    def __str__(self) -> str:
        return f"{self.product.name} / {self.service_key}"


class Pricing(models.Model):
    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Mensal"
        ANNUAL = "annual", "Anual"
        LIFETIME = "lifetime", "Vitalício"
        ONE_TIME = "one_time", "Cobrança Única"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="pricings")
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    trial_days = models.IntegerField(default=0)
    max_api_calls = models.IntegerField(default=10000)
    max_users = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_pricings"
        unique_together = [("product", "billing_cycle")]

    def __str__(self) -> str:
        return f"{self.product.name} / {self.billing_cycle} / R${self.amount}"
