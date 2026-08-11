from django.db import models


class KeycloakConnection(models.Model):
    """Linha única (pk=1): a conexão do PaperMoon com o Keycloak que ELE
    administra via Admin REST API pra provisionar realms/clients de clientes
    (produto "Keycloak IAM/SSO", ver apps.products.models e
    apps.provisioning.keycloak.KeycloakProvisioner).

    NÃO confundir com apps.accounts.SSOConfiguration — aquilo é o SSO de
    STAFF (como o time do PaperMoon entra no próprio backoffice). São
    Keycloaks diferentes, com propósitos diferentes; o único ponto em comum
    é reaproveitar o mesmo padrão de config runtime + secret criptografado.

    `admin_token_encrypted` nunca é exposto em texto puro pela API — apenas
    `admin_token_set` (bool). Criptografado com Fernet (shared/crypto.py,
    mesmo mecanismo do SSOConfiguration.client_secret_encrypted).
    """

    enabled = models.BooleanField(default=False)
    api_url = models.CharField(max_length=500, blank=True)
    admin_token_encrypted = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        "accounts.CustomUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        db_table = "provisioning_keycloak_connection"

    def __str__(self) -> str:
        return f"KeycloakConnection(enabled={self.enabled})"

    @classmethod
    def get_solo(cls) -> "KeycloakConnection":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
