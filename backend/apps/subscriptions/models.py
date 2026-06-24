import secrets
from uuid import uuid4

from django.db import models


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Ativo"
        GRACE_PERIOD = "grace_period", "Período de Tolerância"
        EXPIRED = "expired", "Expirado"
        CANCELLED = "cancelled", "Cancelado"
        SUSPENDED = "suspended", "Suspenso"

    _TRANSITIONS: dict[str, set[str]] = {
        Status.TRIAL: {Status.ACTIVE, Status.CANCELLED, Status.EXPIRED},
        Status.ACTIVE: {Status.GRACE_PERIOD, Status.CANCELLED, Status.SUSPENDED},
        Status.GRACE_PERIOD: {Status.ACTIVE, Status.EXPIRED, Status.CANCELLED},
        Status.EXPIRED: {Status.ACTIVE, Status.CANCELLED},
        Status.SUSPENDED: {Status.ACTIVE, Status.CANCELLED},
        Status.CANCELLED: set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    pricing = models.ForeignKey(
        "products.Pricing",
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions"

    def __str__(self) -> str:
        return f"{self.customer} / {self.product} / {self.status}"

    def transition_to(self, new_status: str) -> None:
        allowed = self._TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid transition: {self.status} → {new_status}")
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])


class License(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        GRACE_PERIOD = "grace_period", "Período de Tolerância"
        EXPIRED = "expired", "Expirado"
        SUSPENDED = "suspended", "Suspenso"
        REVOKED = "revoked", "Revogado"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    subscription = models.OneToOneField(
        Subscription, on_delete=models.PROTECT, related_name="license"
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="licenses",
    )
    key = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "licenses"

    def __str__(self) -> str:
        return f"License({self.subscription_id} {self.status})"

    @classmethod
    def generate_key(cls) -> str:
        return secrets.token_urlsafe(48)

    def is_valid(self) -> bool:
        from django.utils import timezone

        return self.status == self.Status.ACTIVE and self.valid_until > timezone.now()


class ServiceAccess(models.Model):
    """Tracks provisioning state for each microservice within a License."""

    class Status(models.TextChoices):
        PROVISIONING = "provisioning", "Provisionando"
        ACTIVE = "active", "Ativo"
        SUSPENDED = "suspended", "Suspenso"
        FAILED = "failed", "Falhou"
        DEPROVISIONED = "deprovisioned", "Desprovisionado"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    license = models.ForeignKey(License, on_delete=models.PROTECT, related_name="service_accesses")
    service_key = models.CharField(max_length=50, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROVISIONING, db_index=True
    )
    external_id = models.CharField(max_length=255, null=True, blank=True)
    config = models.JSONField(default=dict, blank=True)
    provisioned_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_accesses"
        unique_together = [("license", "service_key")]
        indexes = [
            models.Index(fields=["service_key", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.license_id} / {self.service_key} / {self.status}"
