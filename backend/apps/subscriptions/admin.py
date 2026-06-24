from django.contrib import admin

from apps.subscriptions.models import License, ServiceAccess, Subscription


class ServiceAccessInline(admin.TabularInline):
    model = ServiceAccess
    extra = 0
    fields = ["service_key", "status", "external_id", "provisioned_at", "suspended_at", "error"]
    readonly_fields = ["provisioned_at", "suspended_at"]


class LicenseInline(admin.StackedInline):
    model = License
    extra = 0
    fields = ["key", "status", "valid_from", "valid_until", "revoked_at"]
    readonly_fields = ["key", "valid_from", "valid_until", "revoked_at"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["customer", "product", "status", "starts_at", "expires_at", "created_at"]
    list_filter = ["status", "product"]
    search_fields = ["customer__company_name", "product__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [LicenseInline]
    actions = ["mark_suspended"]

    @admin.action(description="Suspender assinaturas selecionadas")
    def mark_suspended(self, request, queryset):
        from apps.subscriptions.commands import SuspendSubscriptionCommand

        cmd = SuspendSubscriptionCommand()
        for sub in queryset.filter(status=Subscription.Status.ACTIVE):
            cmd.execute(sub.id, reason="admin_action")
        self.message_user(request, f"{queryset.count()} assinatura(s) suspensa(s).")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ["customer", "status", "valid_from", "valid_until", "created_at"]
    list_filter = ["status"]
    search_fields = ["customer__company_name", "key"]
    readonly_fields = ["id", "key", "created_at", "revoked_at"]
    inlines = [ServiceAccessInline]


@admin.register(ServiceAccess)
class ServiceAccessAdmin(admin.ModelAdmin):
    list_display = ["license", "service_key", "status", "external_id", "provisioned_at"]
    list_filter = ["service_key", "status"]
    search_fields = ["license__customer__company_name", "external_id"]
    readonly_fields = ["id", "created_at", "updated_at", "provisioned_at", "suspended_at"]
    actions = ["reprovision_failed"]

    @admin.action(description="Re-provisionar serviços com falha")
    def reprovision_failed(self, request, queryset):
        from shared.models import OutboxEvent

        count = 0
        for sa in queryset.filter(
            status__in=[ServiceAccess.Status.FAILED, ServiceAccess.Status.PROVISIONING]
        ).select_related("license"):
            sa.status = ServiceAccess.Status.PROVISIONING
            sa.error = None
            sa.save(update_fields=["status", "error", "updated_at"])
            OutboxEvent.objects.create(
                event_type="service_access.provision",
                payload={
                    "service_access_id": str(sa.id),
                    "license_id": str(sa.license_id),
                    "customer_id": str(sa.license.customer_id),
                    "service_key": sa.service_key,
                    "config": sa.config,
                },
            )
            count += 1
        self.message_user(request, f"{count} serviço(s) enviado(s) para re-provisionamento.")
