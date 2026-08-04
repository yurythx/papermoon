from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "accounts_users"


class SSOConfiguration(models.Model):
    """
    Linha única (pk=1) com a configuração de SSO de staff, editável em runtime pelo
    backoffice (Configurações). Ver docs/backend/sso-keycloak-integration.md.

    `client_secret_encrypted` nunca é exposto em texto puro pela API — apenas
    `client_secret_set` (bool). Criptografado com Fernet (shared/crypto.py).
    """

    enabled = models.BooleanField(default=False)
    issuer = models.CharField(max_length=500, blank=True)
    client_id = models.CharField(max_length=255, blank=True)
    client_secret_encrypted = models.TextField(blank=True)
    # Nome do grupo/role do Keycloak (claim "groups" do id_token) que autoriza
    # criar automaticamente (JIT) uma conta staff no primeiro login SSO de um
    # e-mail ainda não cadastrado. Vazio = JIT desativado (só quem já existe
    # como staff consegue logar via SSO) — ver ADR 0002.
    staff_group = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "accounts.CustomUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        db_table = "accounts_sso_configuration"

    def __str__(self) -> str:
        return f"SSOConfiguration(enabled={self.enabled})"

    @classmethod
    def get_solo(cls) -> "SSOConfiguration":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
