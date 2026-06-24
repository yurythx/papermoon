from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0005_alter_servicecomponent_service_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servicecomponent",
            name="service_key",
            field=models.CharField(
                choices=[
                    ("chatwoot", "Chatwoot"),
                    ("meta_whatsapp", "WhatsApp API Meta"),
                    ("n8n", "n8n Automação"),
                    ("glpi", "GLPI Helpdesk"),
                    ("zabbix", "Zabbix Monitoramento"),
                    ("proxmox", "Proxmox VE"),
                    ("truenas", "TrueNAS"),
                    ("nextcloud", "Nextcloud"),
                    ("aapanel", "AAPanel"),
                    ("evolution_api", "Evolution API"),
                    ("rustdesk", "RustDesk"),
                    ("samba", "Samba File Server"),
                    ("windows-server", "Windows Server / AD"),
                    ("plone", "Plone CMS"),
                    ("keycloak", "Keycloak IAM/SSO"),
                    ("tailscale", "Tailscale"),
                    ("twenty_crm", "Twenty CRM"),
                    ("papermark", "Papermark"),
                    ("crowdsec", "CrowdSec"),
                ],
                max_length=50,
            ),
        ),
    ]
