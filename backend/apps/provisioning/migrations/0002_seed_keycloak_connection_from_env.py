"""Migração de dados, idempotente: se KEYCLOAK_API_URL/KEYCLOAK_ADMIN_TOKEN
existirem no ambiente (.env), popula a linha pk=1 de KeycloakConnection com
elas — preserva o bootstrap via variável de ambiente num deploy novo, sem
exigir que alguém abra o backoffice manualmente antes de qualquer coisa
funcionar. Depois desta migração, nenhum código de runtime lê essas duas
env vars diretamente — só apps.provisioning.keycloak_config."""

from django.conf import settings
from django.db import migrations

from shared.crypto import encrypt_secret


def seed_from_env(apps, schema_editor):
    api_url = (getattr(settings, "KEYCLOAK_API_URL", "") or "").rstrip("/")
    admin_token = getattr(settings, "KEYCLOAK_ADMIN_TOKEN", "") or ""
    if not (api_url and admin_token):
        return

    KeycloakConnection = apps.get_model("provisioning", "KeycloakConnection")
    row, _ = KeycloakConnection.objects.get_or_create(pk=1)
    row.enabled = True
    row.api_url = api_url
    row.admin_token_encrypted = encrypt_secret(admin_token)
    row.save()


class Migration(migrations.Migration):
    dependencies = [
        ("provisioning", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_from_env, reverse_code=migrations.RunPython.noop),
    ]
