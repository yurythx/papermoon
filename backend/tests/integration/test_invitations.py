"""Integration tests for the Invitation feature."""

import pytest

from apps.customers.models import Customer, CustomerProfile, Invitation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_customer_with_owner(email="owner@test.com", doc="40.000.000/0001-40"):
    from apps.accounts.models import CustomUser

    user = CustomUser.objects.create_user(
        username=email.split("@")[0], email=email, password="pass1234"
    )
    customer = Customer.objects.create(company_name="Invite Corp", document=doc)
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)
    return customer, user


def _auth_client_for(user, password="pass1234"):
    from rest_framework.test import APIClient

    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": password},
        format="json",
    )
    token = resp.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ---------------------------------------------------------------------------
# Create invitation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateInvitation:
    def test_owner_can_send_invite(self):
        customer, owner = _make_customer_with_owner(doc="41.000.000/0001-41")
        client = _auth_client_for(owner)

        resp = client.post(
            "/api/v1/client/invitations/",
            {"email": "newmember@test.com", "role": "member"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["email"] == "newmember@test.com"
        assert data["status"] == "pending"

    def test_create_emits_invitation_created_outbox_event(self):
        from shared.models import OutboxEvent

        customer, owner = _make_customer_with_owner(doc="42.000.000/0001-42")
        client = _auth_client_for(owner)
        client.post(
            "/api/v1/client/invitations/",
            {"email": "evt@test.com", "role": "member"},
            format="json",
        )
        assert OutboxEvent.objects.filter(event_type="invitation.created").exists()

    def test_member_cannot_send_invite(self):
        from apps.accounts.models import CustomUser

        customer, owner = _make_customer_with_owner(doc="43.000.000/0001-43")
        member = CustomUser.objects.create_user(
            username="member1", email="member1@test.com", password="pass1234"
        )
        CustomerProfile.objects.create(
            user=member, customer=customer, role=CustomerProfile.Role.MEMBER
        )
        client = _auth_client_for(member)
        resp = client.post(
            "/api/v1/client/invitations/",
            {"email": "other@test.com", "role": "member"},
            format="json",
        )
        assert resp.status_code == 403

    def test_resending_to_same_email_is_idempotent(self):
        customer, owner = _make_customer_with_owner(doc="44.000.000/0001-44")
        client = _auth_client_for(owner)
        client.post(
            "/api/v1/client/invitations/",
            {"email": "idempotent@test.com", "role": "member"},
            format="json",
        )
        resp2 = client.post(
            "/api/v1/client/invitations/",
            {"email": "idempotent@test.com", "role": "member"},
            format="json",
        )
        assert resp2.status_code == 201
        assert (
            Invitation.objects.filter(
                customer=customer, email="idempotent@test.com", status="pending"
            ).count()
            == 1
        )

    def test_list_invitations_returns_own_customer_only(self):
        customer, owner = _make_customer_with_owner(doc="45.000.000/0001-45")
        client = _auth_client_for(owner)
        client.post("/api/v1/client/invitations/", {"email": "a@test.com"}, format="json")
        client.post("/api/v1/client/invitations/", {"email": "b@test.com"}, format="json")

        resp = client.get("/api/v1/client/invitations/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_unauthenticated_cannot_create_invite(self, api_client):
        resp = api_client.post(
            "/api/v1/client/invitations/",
            {"email": "x@x.com"},
            format="json",
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Accept invitation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAcceptInvitation:
    def _create_invitation(self, email="invitee@test.com", doc="46.000.000/0001-46"):
        customer, owner = _make_customer_with_owner(doc=doc)
        client = _auth_client_for(owner)
        client.post(
            "/api/v1/client/invitations/",
            {"email": email, "role": "member"},
            format="json",
        )
        return Invitation.objects.get(customer=customer, email=email)

    def test_accept_creates_user_and_profile(self, api_client):
        invitation = self._create_invitation(doc="47.000.000/0001-47")
        resp = api_client.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "securepass1"},
            format="json",
        )
        assert resp.status_code == 201
        from apps.accounts.models import CustomUser

        assert CustomUser.objects.filter(email=invitation.email).exists()
        assert CustomerProfile.objects.filter(
            user__email=invitation.email, customer=invitation.customer
        ).exists()

    def test_accept_marks_invitation_as_accepted(self, api_client):
        invitation = self._create_invitation(doc="48.000.000/0001-48")
        api_client.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "securepass1"},
            format="json",
        )
        invitation.refresh_from_db()
        assert invitation.status == Invitation.Status.ACCEPTED
        assert invitation.accepted_at is not None

    def test_accept_invalid_token_returns_400(self, api_client):
        resp = api_client.post(
            "/api/v1/invitations/accept/",
            {"token": "this-token-does-not-exist", "password": "pass1234"},
            format="json",
        )
        assert resp.status_code == 400

    def test_accept_already_accepted_token_returns_400(self, api_client):
        invitation = self._create_invitation(doc="49.000.000/0001-49")
        api_client.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "securepass1"},
            format="json",
        )
        resp2 = api_client.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "securepass1"},
            format="json",
        )
        assert resp2.status_code == 400

    def test_accept_expired_token_returns_400(self, api_client):
        from django.utils import timezone

        invitation = self._create_invitation(doc="50.000.000/0001-50")
        invitation.expires_at = timezone.now() - __import__("datetime").timedelta(days=1)
        invitation.save()
        resp = api_client.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "securepass1"},
            format="json",
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Revoke invitation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRevokeInvitation:
    def test_owner_can_revoke_invitation(self):
        customer, owner = _make_customer_with_owner(doc="51.000.000/0001-51")
        client = _auth_client_for(owner)
        create_resp = client.post(
            "/api/v1/client/invitations/",
            {"email": "revoke@test.com", "role": "member"},
            format="json",
        )
        inv_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"/api/v1/client/invitations/{inv_id}/")
        assert resp.status_code == 204

        invitation = Invitation.objects.get(pk=inv_id)
        assert invitation.status == Invitation.Status.REVOKED

    def test_member_cannot_revoke_invitation(self):
        from apps.accounts.models import CustomUser

        customer, owner = _make_customer_with_owner(doc="52.000.000/0001-52")
        owner_client = _auth_client_for(owner)
        create_resp = owner_client.post(
            "/api/v1/client/invitations/",
            {"email": "torevoke@test.com", "role": "member"},
            format="json",
        )
        inv_id = create_resp.json()["data"]["id"]

        member = CustomUser.objects.create_user(
            username="member52", email="member52@test.com", password="pass1234"
        )
        CustomerProfile.objects.create(
            user=member, customer=customer, role=CustomerProfile.Role.MEMBER
        )
        member_client = _auth_client_for(member)

        resp = member_client.delete(f"/api/v1/client/invitations/{inv_id}/")
        assert resp.status_code == 403

    def test_revoke_already_accepted_returns_400(self):
        customer, owner = _make_customer_with_owner(doc="53.000.000/0001-53")
        owner_client = _auth_client_for(owner)
        create_resp = owner_client.post(
            "/api/v1/client/invitations/",
            {"email": "toaccept@test.com", "role": "member"},
            format="json",
        )
        inv_id = create_resp.json()["data"]["id"]

        # Accept it first
        from rest_framework.test import APIClient

        api = APIClient()
        invitation = Invitation.objects.get(pk=inv_id)
        api.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "pass1234"},
            format="json",
        )

        resp = owner_client.delete(f"/api/v1/client/invitations/{inv_id}/")
        assert resp.status_code == 400

    def test_revoke_nonexistent_invitation_returns_404(self):
        import uuid

        _, owner = _make_customer_with_owner(doc="54.000.000/0001-54")
        client = _auth_client_for(owner)
        resp = client.delete(f"/api/v1/client/invitations/{uuid.uuid4()}/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Accept invitation — edge cases
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAcceptInvitationEdgeCases:
    def test_accept_with_already_registered_email_returns_400(self, api_client):
        from apps.accounts.models import CustomUser

        customer, owner = _make_customer_with_owner(doc="55.000.000/0001-55")
        existing_email = "existing@test.com"
        CustomUser.objects.create_user(
            username="existinguser", email=existing_email, password="pass1234"
        )
        owner_client = _auth_client_for(owner)
        owner_client.post(
            "/api/v1/client/invitations/",
            {"email": existing_email, "role": "member"},
            format="json",
        )
        invitation = Invitation.objects.get(customer=customer, email=existing_email)

        resp = api_client.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "pass1234"},
            format="json",
        )
        assert resp.status_code == 400

    def test_accept_deduplicates_username_when_collision(self, api_client):
        from apps.accounts.models import CustomUser

        customer, owner = _make_customer_with_owner(doc="56.000.000/0001-56")
        collision_email = "dup@test.com"
        # Pre-create a user with the same username prefix "dup"
        CustomUser.objects.create_user(username="dup", email="dup_other@test.com", password="x")

        owner_client = _auth_client_for(owner)
        owner_client.post(
            "/api/v1/client/invitations/",
            {"email": collision_email, "role": "member"},
            format="json",
        )
        invitation = Invitation.objects.get(customer=customer, email=collision_email)

        resp = api_client.post(
            "/api/v1/invitations/accept/",
            {"token": invitation.token, "password": "pass1234"},
            format="json",
        )
        assert resp.status_code == 201
        # Username should be "dup1" since "dup" was taken
        user = CustomUser.objects.get(email=collision_email)
        assert user.username == "dup1"


# ---------------------------------------------------------------------------
# Resend invitation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestResendInvitation:
    def _create_pending_invite(self, doc="57.000.000/0001-57", email="resend@test.com"):
        customer, owner = _make_customer_with_owner(doc=doc, email=f"owner_{doc[:2]}@test.com")
        client = _auth_client_for(owner)
        resp = client.post(
            "/api/v1/client/invitations/",
            {"email": email, "role": "member"},
            format="json",
        )
        inv_id = resp.json()["data"]["id"]
        invitation = Invitation.objects.get(pk=inv_id)
        return client, owner, customer, invitation

    def test_owner_can_resend_pending_invitation(self):
        client, _, _, invitation = self._create_pending_invite(doc="57.000.000/0001-57")
        old_token = invitation.token

        resp = client.post(f"/api/v1/client/invitations/{invitation.id}/resend/")
        assert resp.status_code == 200

        invitation.refresh_from_db()
        assert invitation.token != old_token
        assert invitation.status == Invitation.Status.PENDING

    def test_resend_extends_expiry(self):
        from django.utils import timezone

        client, _, _, invitation = self._create_pending_invite(doc="58.000.000/0001-58")
        before_resend = timezone.now()

        resp = client.post(f"/api/v1/client/invitations/{invitation.id}/resend/")
        assert resp.status_code == 200

        invitation.refresh_from_db()
        assert invitation.expires_at > before_resend

    def test_resend_emits_outbox_event(self):
        from shared.models import OutboxEvent

        client, _, _, invitation = self._create_pending_invite(doc="59.000.000/0001-59")
        before_count = OutboxEvent.objects.filter(event_type="invitation.created").count()

        client.post(f"/api/v1/client/invitations/{invitation.id}/resend/")

        assert OutboxEvent.objects.filter(event_type="invitation.created").count() > before_count

    def test_resend_expired_invitation_succeeds(self):
        from datetime import timedelta

        from django.utils import timezone

        client, _, _, invitation = self._create_pending_invite(doc="60.000.000/0001-60")
        invitation.expires_at = timezone.now() - timedelta(days=1)
        invitation.status = Invitation.Status.EXPIRED
        invitation.save()

        resp = client.post(f"/api/v1/client/invitations/{invitation.id}/resend/")
        assert resp.status_code == 200

        invitation.refresh_from_db()
        assert invitation.status == Invitation.Status.PENDING
        assert invitation.expires_at > timezone.now()

    def test_member_cannot_resend_invitation(self):
        from apps.accounts.models import CustomUser

        client, _, customer, invitation = self._create_pending_invite(doc="61.000.000/0001-61")
        member = CustomUser.objects.create_user(
            username="member61", email="member61@test.com", password="pass1234"
        )
        from apps.customers.models import CustomerProfile

        CustomerProfile.objects.create(
            user=member, customer=customer, role=CustomerProfile.Role.MEMBER
        )
        member_client = _auth_client_for(member)

        resp = member_client.post(f"/api/v1/client/invitations/{invitation.id}/resend/")
        assert resp.status_code == 403

    def test_resend_accepted_invitation_returns_400(self):
        client, _, _, invitation = self._create_pending_invite(doc="62.000.000/0001-62")
        invitation.status = Invitation.Status.ACCEPTED
        invitation.save()

        resp = client.post(f"/api/v1/client/invitations/{invitation.id}/resend/")
        assert resp.status_code == 400

    def test_resend_revoked_invitation_returns_400(self):
        client, _, _, invitation = self._create_pending_invite(doc="63.000.000/0001-63")
        invitation.status = Invitation.Status.REVOKED
        invitation.save()

        resp = client.post(f"/api/v1/client/invitations/{invitation.id}/resend/")
        assert resp.status_code == 400

    def test_resend_nonexistent_invitation_returns_404(self):
        import uuid

        _, owner, _, _ = self._create_pending_invite(doc="64.000.000/0001-64")
        client = _auth_client_for(owner)
        resp = client.post(f"/api/v1/client/invitations/{uuid.uuid4()}/resend/")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# max_users enforcement
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMaxUsersEnforcement:
    def test_invite_blocked_when_max_users_reached(self):
        import datetime

        from django.utils import timezone

        from apps.products.models import Pricing, Product
        from apps.subscriptions.models import Subscription

        customer, owner = _make_customer_with_owner(
            doc="65.000.000/0001-65", email="owner65@test.com"
        )

        product = Product.objects.create(name="Starter65", slug="starter-65")
        pricing = Pricing.objects.create(
            product=product,
            billing_cycle="monthly",
            amount="199.00",
            max_users=2,  # owner already counts as 1
        )
        Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=timezone.now(),
            expires_at=timezone.now() + datetime.timedelta(days=30),
        )

        # Fill the remaining slot with a pending invitation
        client = _auth_client_for(owner)
        resp1 = client.post(
            "/api/v1/client/invitations/",
            {"email": "slot1@test.com", "role": "member"},
            format="json",
        )
        assert resp1.status_code == 201  # 1 member + 1 pending = 2 = limit

        # Second invite must be blocked
        resp2 = client.post(
            "/api/v1/client/invitations/",
            {"email": "slot2@test.com", "role": "member"},
            format="json",
        )
        assert resp2.status_code == 400
        assert "max_users" in str(resp2.json())

    def test_invite_allowed_when_no_active_subscription(self):
        """Without an active subscription there is no enforced max_users limit."""
        customer, owner = _make_customer_with_owner(
            doc="66.000.000/0001-66", email="owner66@test.com"
        )
        client = _auth_client_for(owner)

        for i in range(10):
            resp = client.post(
                "/api/v1/client/invitations/",
                {"email": f"user{i}@test.com", "role": "member"},
                format="json",
            )
            assert resp.status_code == 201
