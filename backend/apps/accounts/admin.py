from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest

from apps.accounts.models import CustomUser, SSOConfiguration


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "is_staff", "is_active", "created_at")
    search_fields = ("email", "username")
    ordering = ("-created_at",)
    fieldsets = (*UserAdmin.fieldsets, ("Dados extras", {"fields": ("phone",)}))


@admin.register(SSOConfiguration)
class SSOConfigurationAdmin(admin.ModelAdmin):
    """
    Só leitura para o segredo — a criptografia (shared/crypto.py) assume que
    client_secret_encrypted só é escrito via apps.accounts.sso_config.update_sso_config,
    nunca digitado direto no Django Admin. Editar SSO é feito no backoffice.
    """

    list_display = ("enabled", "issuer", "client_id", "updated_at", "updated_by")
    readonly_fields = ("client_secret_encrypted", "updated_at")
    fields = (
        "enabled",
        "issuer",
        "client_id",
        "client_secret_encrypted",
        "updated_by",
        "updated_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SSOConfiguration.objects.exists()

    def has_delete_permission(
        self, request: HttpRequest, obj: SSOConfiguration | None = None
    ) -> bool:
        return False
