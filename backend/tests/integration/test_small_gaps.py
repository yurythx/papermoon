"""
Targeted tests for remaining 1-6 line gaps across multiple files.
"""

import datetime
from unittest.mock import patch
import uuid

from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.billing.models import Invoice
from apps.customers.models import Customer, CustomerProfile
from apps.licensing.models import ApiKey

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc() -> str:
    d = f"{uuid.uuid4().int % 10**14:014d}"
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def _make_customer_with_owner() -> tuple[Customer, CustomUser]:
    email = f"gap_{uuid.uuid4().hex[:6]}@x.com"
    user = CustomUser.objects.create_user(
        username=email.split("@")[0], email=email, password="pass1234"
    )
    customer = Customer.objects.create(company_name="Gap Co", document=_doc())
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)
    return customer, user


def _auth_client(email: str, password: str = "pass1234") -> APIClient:
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    token = resp.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _login_response(email: str, password: str = "pass1234") -> dict:
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    return resp.json()["data"]


# ---------------------------------------------------------------------------
# accounts/views.py — logout missing token + invalid token (lines 41, 45-46)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLogoutEdgeCases:
    def test_logout_missing_refresh_returns_400(self, api_client, regular_user):
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.post("/api/v1/auth/logout/", {}, format="json")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "missing_token"

    def test_logout_invalid_token_returns_400(self, api_client, regular_user):
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.post(
            "/api/v1/auth/logout/",
            {"refresh": "this.is.not.a.valid.token"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_token"


# ---------------------------------------------------------------------------
# accounts/views.py — password reset confirm with invalid UID (lines 135-136)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPasswordResetConfirmInvalidUID:
    def test_invalid_uid_returns_400(self, api_client):
        resp = api_client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": "not_valid_base64_uid", "token": "sometoken", "password": "newpass123"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_token"


# ---------------------------------------------------------------------------
# customers/repositories.py — get_by_id raises NotFound (lines 14-15)
# customers/repositories.py — get_all returns queryset (line 18)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerRepository:
    def test_get_by_id_raises_not_found_for_unknown_id(self):
        from apps.customers.repositories import DjangoCustomerRepository

        repo = DjangoCustomerRepository()
        with pytest.raises(Exception):  # NotFound (rest_framework)
            repo.get_by_id(uuid.uuid4())

    def test_get_all_returns_queryset(self):
        from apps.customers.repositories import DjangoCustomerRepository

        Customer.objects.create(company_name="Repo Co", document=_doc())
        repo = DjangoCustomerRepository()
        qs = repo.get_all()
        assert qs.count() >= 1


# ---------------------------------------------------------------------------
# customers/views_client.py — invoice list with ?status filter (line 67)
# customers/views_client.py — team list (lines 138-155)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientViewsMissing:
    def test_invoice_list_with_status_filter(self):
        customer, user = _make_customer_with_owner()
        Invoice.objects.create(
            customer=customer,
            amount="50.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PAID,
        )
        Invoice.objects.create(
            customer=customer,
            amount="60.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PENDING,
        )

        client = _auth_client(user.email)
        resp = client.get("/api/v1/client/invoices/?status=paid")
        assert resp.status_code == 200
        results = resp.json()["data"]["results"]
        assert all(item["status"] == "paid" for item in results)

    def test_team_list_returns_members(self):
        customer, user = _make_customer_with_owner()
        # Add a second member
        email2 = f"member_{uuid.uuid4().hex[:6]}@x.com"
        user2 = CustomUser.objects.create_user(
            username=email2.split("@")[0], email=email2, password="x"
        )
        CustomerProfile.objects.create(
            user=user2, customer=customer, role=CustomerProfile.Role.MEMBER
        )

        client = _auth_client(user.email)
        resp = client.get("/api/v1/client/team/")
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
        assert len(resp.json()["data"]) >= 2

    def test_team_list_marks_is_you_for_current_user(self):
        customer, user = _make_customer_with_owner()
        client = _auth_client(user.email)
        resp = client.get("/api/v1/client/team/")
        assert resp.status_code == 200
        me = next(m for m in resp.json()["data"] if m["email"] == user.email)
        assert me["is_you"] is True

    def test_team_member_role_change(self):
        customer, owner = _make_customer_with_owner()
        email2 = f"member_{uuid.uuid4().hex[:6]}@x.com"
        user2 = CustomUser.objects.create_user(
            username=email2.split("@")[0], email=email2, password="pass1234"
        )
        profile2 = CustomerProfile.objects.create(
            user=user2, customer=customer, role=CustomerProfile.Role.MEMBER
        )

        client = _auth_client(owner.email)
        resp = client.patch(f"/api/v1/client/team/{profile2.pk}/", {"role": "admin"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "admin"
        profile2.refresh_from_db()
        assert profile2.role == "admin"

    def test_team_member_remove(self):
        customer, owner = _make_customer_with_owner()
        email2 = f"member_{uuid.uuid4().hex[:6]}@x.com"
        user2 = CustomUser.objects.create_user(
            username=email2.split("@")[0], email=email2, password="pass1234"
        )
        profile2 = CustomerProfile.objects.create(
            user=user2, customer=customer, role=CustomerProfile.Role.MEMBER
        )

        client = _auth_client(owner.email)
        resp = client.delete(f"/api/v1/client/team/{profile2.pk}/")
        assert resp.status_code == 204
        assert not CustomerProfile.objects.filter(pk=profile2.pk).exists()

    def test_team_member_cannot_change_owner_role(self):
        customer, owner = _make_customer_with_owner()
        owner_profile = CustomerProfile.objects.get(user=owner, customer=customer)

        # Another admin tries to change owner's role
        email2 = f"admin_{uuid.uuid4().hex[:6]}@x.com"
        user2 = CustomUser.objects.create_user(
            username=email2.split("@")[0], email=email2, password="pass1234"
        )
        CustomerProfile.objects.create(
            user=user2, customer=customer, role=CustomerProfile.Role.ADMIN
        )

        client = _auth_client(user2.email)
        resp = client.patch(
            f"/api/v1/client/team/{owner_profile.pk}/", {"role": "member"}, format="json"
        )
        assert resp.status_code == 403

    def test_team_member_non_manager_cannot_remove(self):
        customer, owner = _make_customer_with_owner()
        email2 = f"member_{uuid.uuid4().hex[:6]}@x.com"
        user2 = CustomUser.objects.create_user(
            username=email2.split("@")[0], email=email2, password="pass1234"
        )
        profile2 = CustomerProfile.objects.create(
            user=user2, customer=customer, role=CustomerProfile.Role.MEMBER
        )

        # Non-manager (member) tries to remove another member
        email3 = f"other_{uuid.uuid4().hex[:6]}@x.com"
        user3 = CustomUser.objects.create_user(
            username=email3.split("@")[0], email=email3, password="pass1234"
        )
        CustomerProfile.objects.create(
            user=user3, customer=customer, role=CustomerProfile.Role.MEMBER
        )

        client = _auth_client(user3.email)
        resp = client.delete(f"/api/v1/client/team/{profile2.pk}/")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# billing/views.py — webhook with unknown asaas_id (lines 49-51)
# billing/views.py — admin billing list with filters (lines 87, 92-93)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBillingViewsMissing:
    def test_webhook_unknown_asaas_id_returns_200(self, api_client):
        from django.test import override_settings

        with override_settings(ASAAS_WEBHOOK_TOKEN="test-webhook-token"):
            resp = api_client.post(
                "/api/v1/webhooks/asaas/",
                {"event": "PAYMENT_RECEIVED", "payment": {"id": "nonexistent-id"}},
                format="json",
                HTTP_ASAAS_ACCESS_TOKEN="test-webhook-token",
            )
        # Returns 200 with received=True even for unknown IDs
        assert resp.status_code == 200

    def test_admin_billing_list_filter_by_status(self, admin_client):
        customer, _ = _make_customer_with_owner()
        Invoice.objects.create(
            customer=customer,
            amount="99.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PAID,
        )
        resp = admin_client.get("/api/v1/admin/billing/invoices/?status=paid")
        assert resp.status_code == 200

    def test_admin_billing_list_filter_by_customer_id(self, admin_client):
        customer, _ = _make_customer_with_owner()
        Invoice.objects.create(
            customer=customer,
            amount="99.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PENDING,
        )
        resp = admin_client.get(f"/api/v1/admin/billing/invoices/?customer_id={customer.id}")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# licensing/handlers.py — reactivate_api_keys (lines 67-69)
# licensing/handlers.py — _next_month_start in December (line 74)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLicensingHandlers:
    def test_reactivate_api_keys_handler(self):
        from apps.licensing.handlers import reactivate_api_keys

        customer, _ = _make_customer_with_owner()
        ApiKey.objects.create(customer=customer, key=f"key-{uuid.uuid4().hex}", is_active=False)

        reactivate_api_keys({"customer_id": str(customer.id)}, str(uuid.uuid4()))

        assert ApiKey.objects.filter(customer=customer, is_active=True).exists()

    def test_next_month_start_in_december(self):
        from apps.licensing.handlers import _next_month_start

        dt = timezone.now().replace(year=2024, month=12, day=15)
        result = _next_month_start(dt)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1


# ---------------------------------------------------------------------------
# support/handlers.py — reactivate_chatwoot (lines 22-24)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSupportHandlers:
    def test_reactivate_chatwoot_handler(self):
        from apps.support.handlers import reactivate_chatwoot

        customer, _ = _make_customer_with_owner()

        with patch("apps.support.commands.ChatwootClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.reactivate_agents.return_value = True

            reactivate_chatwoot({"customer_id": str(customer.id)}, str(uuid.uuid4()))

            mock_client.reactivate_agents.assert_called_once_with(str(customer.id))


# ---------------------------------------------------------------------------
# subscriptions/renewal.py — GenerateRenewalInvoiceCommand with unknown sub (lines 33-35)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRenewalCommand:
    def test_unknown_subscription_id_returns_none(self):
        from apps.subscriptions.renewal import GenerateRenewalInvoiceCommand

        result = GenerateRenewalInvoiceCommand().execute(uuid.uuid4())
        assert result is None
