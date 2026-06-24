from datetime import timedelta
import secrets
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.customers.models import Customer, CustomerProfile, Invitation
from shared.models import OutboxEvent

_INVITE_EXPIRY_DAYS = 7

UserModel = get_user_model()


class CreateInvitationCommand:
    """
    Creates an Invitation and emits invitation.created into the Outbox.

    Only owners and admins may invite; members may not.
    Re-sending to the same email (while the previous invite is still pending)
    is idempotent — returns the existing record instead of creating a duplicate.
    """

    def __init__(self, customer_id: UUID, email: str, role: str, invited_by_id: UUID) -> None:
        self._customer_id = customer_id
        self._email = email
        self._role = role
        self._invited_by_id = invited_by_id

    @transaction.atomic
    def execute(self) -> Invitation:
        try:
            customer = Customer.objects.get(pk=self._customer_id)
        except Customer.DoesNotExist as exc:
            raise NotFound("Customer não encontrado.") from exc

        inviter_profile = CustomerProfile.objects.filter(
            user_id=self._invited_by_id, customer=customer
        ).first()
        if not inviter_profile or inviter_profile.role == CustomerProfile.Role.MEMBER:
            raise PermissionDenied("Apenas owners e admins podem convidar membros.")

        # Idempotency: reuse a pending invite for the same email
        existing = Invitation.objects.filter(
            customer=customer,
            email=self._email,
            status=Invitation.Status.PENDING,
        ).first()
        if existing and not existing.is_expired():
            return existing

        self._enforce_max_users(customer)

        invitation = Invitation.objects.create(
            customer=customer,
            invited_by_id=self._invited_by_id,
            email=self._email,
            role=self._role,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(days=_INVITE_EXPIRY_DAYS),
        )
        OutboxEvent.objects.create(
            event_type="invitation.created",
            payload={
                "invitation_id": str(invitation.id),
                "customer_id": str(customer.id),
                "email": self._email,
                "invited_by_id": str(self._invited_by_id),
            },
        )
        return invitation

    @staticmethod
    def _enforce_max_users(customer: "Customer") -> None:
        from apps.subscriptions.models import Subscription

        active_sub = (
            Subscription.objects.filter(
                customer=customer,
                status__in=[
                    Subscription.Status.ACTIVE,
                    Subscription.Status.GRACE_PERIOD,
                    Subscription.Status.TRIAL,
                ],
            )
            .select_related("pricing")
            .first()
        )
        if not active_sub:
            return  # no active plan — no enforced limit

        max_users = active_sub.pricing.max_users
        if not max_users:
            return  # 0 means no limit
        current_members = CustomerProfile.objects.filter(customer=customer).count()
        pending_invites = Invitation.objects.filter(
            customer=customer, status=Invitation.Status.PENDING
        ).count()
        if current_members + pending_invites >= max_users:
            raise ValidationError(
                {"max_users": f"Limite de {max_users} usuários do plano atingido."}
            )


class AcceptInvitationCommand:
    """
    Accepts an invitation token, creating a new user and CustomerProfile.

    Validates:
      - token exists and is PENDING
      - token is not expired
      - email is not already registered (would be a duplicate user)
    """

    def __init__(self, token: str, password: str) -> None:
        self._token = token
        self._password = password

    @transaction.atomic
    def execute(self) -> CustomerProfile:
        try:
            invitation = Invitation.objects.select_for_update().get(
                token=self._token,
                status=Invitation.Status.PENDING,
            )
        except Invitation.DoesNotExist as exc:
            raise ValidationError({"token": "Convite inválido ou já utilizado."}) from exc

        if invitation.is_expired():
            invitation.status = Invitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            raise ValidationError({"token": "Este convite expirou."})

        if UserModel.objects.filter(email=invitation.email).exists():
            raise ValidationError({"email": "Este e-mail já possui uma conta."})

        username = invitation.email.split("@")[0]
        base = username
        counter = 1
        while UserModel.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = UserModel.objects.create_user(
            username=username,
            email=invitation.email,
            password=self._password,
        )

        profile = CustomerProfile.objects.create(
            user=user,
            customer=invitation.customer,
            role=invitation.role,
        )

        invitation.status = Invitation.Status.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at"])

        OutboxEvent.objects.create(
            event_type="invitation.accepted",
            payload={
                "invitation_id": str(invitation.id),
                "customer_id": str(invitation.customer_id),
                "user_id": str(user.id),
                "email": invitation.email,
            },
        )
        return profile


class RevokeInvitationCommand:
    """Revokes a pending invitation. Only the inviting customer's owner/admin may revoke."""

    def __init__(self, invitation_id: UUID, revoked_by_id: UUID) -> None:
        self._invitation_id = invitation_id
        self._revoked_by_id = revoked_by_id

    @transaction.atomic
    def execute(self) -> Invitation:
        try:
            invitation = Invitation.objects.select_for_update().get(pk=self._invitation_id)
        except Invitation.DoesNotExist as exc:
            raise NotFound("Convite não encontrado.") from exc

        profile = CustomerProfile.objects.filter(
            user_id=self._revoked_by_id, customer=invitation.customer
        ).first()
        if not profile or profile.role == CustomerProfile.Role.MEMBER:
            raise PermissionDenied("Apenas owners e admins podem revogar convites.")

        if invitation.status != Invitation.Status.PENDING:
            raise ValidationError({"status": "Apenas convites pendentes podem ser revogados."})

        invitation.status = Invitation.Status.REVOKED
        invitation.save(update_fields=["status"])
        return invitation


class ResendInvitationCommand:
    """
    Re-sends a pending (or expired) invitation:
    - Generates a fresh token + new expiry
    - Emits invitation.created into the Outbox so the email handler fires again
    - Only owners and admins may resend; members cannot
    """

    def __init__(self, invitation_id: UUID, requested_by_id: UUID) -> None:
        self._invitation_id = invitation_id
        self._requested_by_id = requested_by_id

    @transaction.atomic
    def execute(self) -> Invitation:
        try:
            invitation = Invitation.objects.select_for_update().get(pk=self._invitation_id)
        except Invitation.DoesNotExist as exc:
            raise NotFound("Convite não encontrado.") from exc

        profile = CustomerProfile.objects.filter(
            user_id=self._requested_by_id, customer=invitation.customer
        ).first()
        if not profile or profile.role == CustomerProfile.Role.MEMBER:
            raise PermissionDenied("Apenas owners e admins podem reenviar convites.")

        if invitation.status not in (Invitation.Status.PENDING, Invitation.Status.EXPIRED):
            raise ValidationError(
                {"status": "Apenas convites pendentes ou expirados podem ser reenviados."}
            )

        invitation.token = secrets.token_urlsafe(48)
        invitation.status = Invitation.Status.PENDING
        invitation.expires_at = timezone.now() + timedelta(days=_INVITE_EXPIRY_DAYS)
        invitation.save(update_fields=["token", "status", "expires_at"])

        OutboxEvent.objects.create(
            event_type="invitation.created",
            payload={
                "invitation_id": str(invitation.id),
                "customer_id": str(invitation.customer_id),
                "email": invitation.email,
                "role": invitation.role,
                "token": invitation.token,
            },
        )
        return invitation
