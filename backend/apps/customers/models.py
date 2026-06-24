from uuid import uuid4

from django.conf import settings
from django.db import models

from shared.models import SoftDeleteManager


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        SUSPENDED = "suspended", "Suspenso"
        CANCELLED = "cancelled", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    document = models.CharField(max_length=18, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    asaas_customer_id = models.CharField(max_length=100, blank=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "customers"

    def __str__(self) -> str:
        return self.company_name

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class Invitation(models.Model):
    """
    Allows an owner/admin to invite an external email to join their tenant.

    Flow:
      1. owner calls POST /api/v1/client/invitations/  → creates this record + OutboxEvent
      2. Celery handler fires send_invitation_email
      3. invitee calls POST /api/v1/invitations/accept/ with token + password
         → CustomUser + CustomerProfile created, invitation marked accepted
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        ACCEPTED = "accepted", "Aceito"
        EXPIRED = "expired", "Expirado"
        REVOKED = "revoked", "Revogado"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_invitations",
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, default="member")
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "customer_invitations"
        indexes = [models.Index(fields=["token", "status"])]

    def __str__(self) -> str:
        return f"Invitation({self.email} {self.status})"

    def is_expired(self) -> bool:
        from django.utils import timezone

        return self.expires_at < timezone.now()


class CustomerProfile(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Proprietário"
        ADMIN = "admin", "Administrador"
        MEMBER = "member", "Membro"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="profiles",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="profiles",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        db_table = "customer_profiles"
        unique_together = [("user", "customer")]

    def __str__(self) -> str:
        return f"CustomerProfile({self.customer_id} {self.role})"
