import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def admin(db):
    from apps.accounts.models import CustomUser

    return CustomUser.objects.create_superuser(
        username="admin_pending",
        email="admin_pending@papermoon.com",
        password="admin123",
    )


@pytest.fixture
def pending_user(db):
    from apps.accounts.models import CustomUser
    from shared.models import OutboxEvent

    user = CustomUser.objects.create_user(
        username="pending@corp.com",
        email="pending@corp.com",
        password="pass123",
        first_name="João",
        last_name="Pendente",
        phone="(11) 98888-0000",
    )
    OutboxEvent.objects.create(
        event_type="user.registered",
        payload={
            "user_id": str(user.id),
            "email": user.email,
            "name": "João Pendente",
            "company_name": "Corp Pendente Ltda",
            "phone": "(11) 98888-0000",
        },
    )
    return user


def _auth(client, email, password):
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    token = resp.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


@pytest.mark.django_db
class TestPendingRegistrationsView:
    URL = "/api/v1/auth/pending-registrations/"

    def test_admin_sees_pending_users(self, client, admin, pending_user):
        _auth(client, admin.email, "admin123")
        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        ids = [item["id"] for item in data]
        assert str(pending_user.id) in ids

    def test_result_includes_company_name_from_outbox(self, client, admin, pending_user):
        _auth(client, admin.email, "admin123")
        resp = client.get(self.URL)
        items = {item["id"]: item for item in resp.json()["data"]}
        item = items[str(pending_user.id)]
        assert item["company_name"] == "Corp Pendente Ltda"
        assert item["phone"] == "(11) 98888-0000"
        assert item["email"] == "pending@corp.com"

    def test_provisioned_user_excluded(self, client, admin, pending_user):
        from apps.customers.models import Customer, CustomerProfile

        customer = Customer.objects.create(
            company_name="Already Corp", document="12.345.678/0001-90"
        )
        CustomerProfile.objects.create(user=pending_user, customer=customer, role="owner")

        _auth(client, admin.email, "admin123")
        resp = client.get(self.URL)
        ids = [item["id"] for item in resp.json()["data"]]
        assert str(pending_user.id) not in ids

    def test_non_admin_gets_403(self, client, pending_user):
        _auth(client, pending_user.email, "pass123")
        resp = client.get(self.URL)
        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, client):
        resp = client.get(self.URL)
        assert resp.status_code == 401


@pytest.mark.django_db
class TestProvisionUserView:
    def _url(self, user_id):
        return f"/api/v1/auth/pending-registrations/{user_id}/provision/"

    def test_admin_can_provision_pending_user(self, client, admin, pending_user):
        from apps.customers.models import Customer, CustomerProfile

        _auth(client, admin.email, "admin123")
        resp = client.post(
            self._url(pending_user.id),
            {"company_name": "Corp Pendente Ltda", "document": "12.345.678/0001-90"},
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["company_name"] == "Corp Pendente Ltda"
        assert Customer.objects.filter(company_name="Corp Pendente Ltda").exists()
        assert CustomerProfile.objects.filter(user=pending_user, role="owner").exists()

    def test_provision_creates_outbox_event(self, client, admin, pending_user):
        from shared.models import OutboxEvent

        _auth(client, admin.email, "admin123")
        client.post(
            self._url(pending_user.id),
            {"company_name": "Corp Nova", "document": "98.765.432/0001-10"},
            format="json",
        )
        assert OutboxEvent.objects.filter(event_type="customer.created").exists()

    def test_provision_already_provisioned_returns_400(self, client, admin, pending_user):
        from apps.customers.models import Customer, CustomerProfile

        customer = Customer.objects.create(
            company_name="Existing Corp", document="11.111.111/0001-11"
        )
        CustomerProfile.objects.create(user=pending_user, customer=customer, role="owner")

        _auth(client, admin.email, "admin123")
        resp = client.post(
            self._url(pending_user.id),
            {"company_name": "Another Corp", "document": "22.222.222/0001-22"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "already_provisioned"

    def test_provision_missing_document_returns_400(self, client, admin, pending_user):
        _auth(client, admin.email, "admin123")
        resp = client.post(
            self._url(pending_user.id),
            {"company_name": "Corp X"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "validation_error"

    def test_provision_unknown_user_returns_404(self, client, admin):
        _auth(client, admin.email, "admin123")
        resp = client.post(
            self._url("00000000-0000-0000-0000-000000000000"),
            {"company_name": "X", "document": "00.000.000/0001-00"},
            format="json",
        )
        assert resp.status_code == 404

    def test_non_admin_gets_403(self, client, pending_user):
        _auth(client, pending_user.email, "pass123")
        resp = client.post(
            self._url(pending_user.id),
            {"company_name": "X", "document": "00.000.000/0001-00"},
            format="json",
        )
        assert resp.status_code == 403
