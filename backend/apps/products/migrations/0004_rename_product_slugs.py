from django.db import migrations


def rename_slugs(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    renames = {
        "whatsapp-api-meta": "whatsapp-api",
        "glpi-helpdesk": "glpi",
        "zabbix-monitoring": "zabbix",
        "proxmox-ve": "proxmox",
    }
    for old_slug, new_slug in renames.items():
        Product.objects.filter(slug=old_slug).update(slug=new_slug)


def reverse_rename_slugs(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    renames = {
        "whatsapp-api": "whatsapp-api-meta",
        "glpi": "glpi-helpdesk",
        "zabbix": "zabbix-monitoring",
        "proxmox": "proxmox-ve",
    }
    for old_slug, new_slug in renames.items():
        Product.objects.filter(slug=old_slug).update(slug=new_slug)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0003_alter_pricing_billing_cycle_and_more"),
    ]

    operations = [
        migrations.RunPython(rename_slugs, reverse_rename_slugs),
    ]
