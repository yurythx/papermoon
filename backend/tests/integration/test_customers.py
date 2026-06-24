import pytest
from rest_framework.test import APIClient

from apps.customers.models import Customer

# ---------------------------------------------------------------------------
# Original fixtures kept for backwards compatibility with existing tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    from apps.accounts.models import CustomUser

    return CustomUser.objects.create_superuser(
        username="admin",
        email="admin@papermoon.com",
        password="admin123",
    )


@pytest.fixture
def auth_client(client, admin_user):
    response = client.post(
        "/api/v1/auth/login/",
        {"email": "admin@papermoon.com", "password": "admin123"},
        format="json",
    )
    token = response.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ---------------------------------------------------------------------------
# Original tests (kept intact)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerAdminEndpoints:
    def test_create_customer_creates_outbox_event(self, auth_client):
        from shared.models import OutboxEvent

        response = auth_client.post(
            "/api/v1/admin/customers/",
            {"company_name": "Empresa X", "document": "11.222.333/0001-81"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "active"

        event = OutboxEvent.objects.get(event_type="customer.created")
        assert event.payload["customer_id"] == data["data"]["id"]

    def test_list_customers_requires_auth(self, client):
        response = client.get("/api/v1/admin/customers/")
        assert response.status_code == 401

    def test_suspend_customer_changes_status(self, auth_client):
        create = auth_client.post(
            "/api/v1/admin/customers/",
            {"company_name": "Empresa Y", "document": "11.111.111/0001-91"},
            format="json",
        )
        customer_id = create.json()["data"]["id"]

        response = auth_client.post(f"/api/v1/admin/customers/{customer_id}/suspend/")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "suspended"

    def test_suspend_already_suspended_returns_400(self, auth_client):
        create = auth_client.post(
            "/api/v1/admin/customers/",
            {"company_name": "Empresa Z", "document": "22.222.222/0001-91"},
            format="json",
        )
        customer_id = create.json()["data"]["id"]

        auth_client.post(f"/api/v1/admin/customers/{customer_id}/suspend/")
        response = auth_client.post(f"/api/v1/admin/customers/{customer_id}/suspend/")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Extended tests (using shared conftest fixtures)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminCustomerList:
    def test_admin_can_list_customers(self, admin_client, customer):
        resp = admin_client.get("/api/v1/admin/customers/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        # paginated response: data.results
        results = data["data"]["results"]
        ids = [c["id"] for c in results]
        assert str(customer.id) in ids

    def test_non_admin_cannot_list(self, customer_client):
        resp = customer_client.get("/api/v1/admin/customers/")
        assert resp.status_code == 403


@pytest.mark.django_db
class TestAdminCustomerDetail:
    def test_admin_retrieves_customer_detail(self, admin_client, customer):
        resp = admin_client.get(f"/api/v1/admin/customers/{customer.id}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(customer.id)

    def test_non_admin_cannot_access_detail(self, customer_client, customer):
        resp = customer_client.get(f"/api/v1/admin/customers/{customer.id}/")
        assert resp.status_code == 403


@pytest.mark.django_db
class TestAdminCustomerReactivate:
    def test_admin_reactivates_suspended_customer(self, admin_client, customer):
        customer.status = Customer.Status.SUSPENDED
        customer.save()
        resp = admin_client.post(f"/api/v1/admin/customers/{customer.id}/reactivate/")
        assert resp.status_code == 200
        customer.refresh_from_db()
        assert customer.status == Customer.Status.ACTIVE

    def test_reactivate_emits_outbox_event(self, admin_client, customer):
        from shared.models import OutboxEvent

        customer.status = Customer.Status.SUSPENDED
        customer.save()
        admin_client.post(f"/api/v1/admin/customers/{customer.id}/reactivate/")
        assert OutboxEvent.objects.filter(event_type="customer.reactivated").exists()


@pytest.mark.django_db
class TestAdminCustomerCancel:
    def test_admin_cancels_customer(self, admin_client, customer):
        resp = admin_client.post(f"/api/v1/admin/customers/{customer.id}/cancel/")
        assert resp.status_code == 200
        customer.refresh_from_db()
        assert customer.status == Customer.Status.CANCELLED

    def test_cancel_emits_outbox_event(self, admin_client, customer):
        from shared.models import OutboxEvent

        admin_client.post(f"/api/v1/admin/customers/{customer.id}/cancel/")
        assert OutboxEvent.objects.filter(event_type="customer.cancelled").exists()


@pytest.mark.django_db
class TestClientMe:
    def test_client_gets_own_profile(self, customer_client, customer_with_profile):
        resp = customer_client.get("/api/v1/client/me/")
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == str(customer_with_profile.id)

    def test_client_updates_company_name(self, customer_client, customer_with_profile):
        resp = customer_client.patch(
            "/api/v1/client/me/",
            {"company_name": "Nome Atualizado"},
            format="json",
        )
        assert resp.status_code == 200
        customer_with_profile.refresh_from_db()
        assert customer_with_profile.company_name == "Nome Atualizado"

    def test_client_cannot_change_status(self, customer_client, customer_with_profile):
        customer_client.patch(
            "/api/v1/client/me/",
            {"status": "cancelled"},
            format="json",
        )
        customer_with_profile.refresh_from_db()
        assert customer_with_profile.status == Customer.Status.ACTIVE

    def test_unauthenticated_cannot_access_me(self, api_client):
        resp = api_client.get("/api/v1/client/me/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestClientInvoices:
    def test_client_lists_own_invoices(self, customer_client, customer_with_profile):
        import datetime

        from apps.billing.models import Invoice

        Invoice.objects.create(
            customer=customer_with_profile,
            amount="100.00",
            due_date=datetime.date.today(),
        )
        resp = customer_client.get("/api/v1/client/invoices/")
        assert resp.status_code == 200
        # ClientInvoiceListView uses paginator, so results key exists
        assert len(resp.json()["data"]["results"]) == 1

    def test_client_invoice_list_hides_untrusted_payment_url(self, customer_client, customer_with_profile):
        import datetime

        from apps.billing.models import Invoice

        Invoice.objects.create(
            customer=customer_with_profile,
            amount="100.00",
            due_date=datetime.date.today(),
            payment_url="https://evil.example.com/pay-123",
        )

        resp = customer_client.get("/api/v1/client/invoices/")

        assert resp.status_code == 200
        assert resp.json()["data"]["results"][0]["payment_url"] is None

    def test_client_cannot_see_other_tenants_invoices(self, customer_client, customer, invoice):
        resp = customer_client.get("/api/v1/client/invoices/")
        invoice_ids = [i["id"] for i in resp.json()["data"]["results"]]
        assert str(invoice.id) not in invoice_ids


@pytest.mark.django_db
class TestClientMetrics:
    def test_client_gets_financial_metrics(self, customer_client, customer_with_profile):
        resp = customer_client.get("/api/v1/client/metrics/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_paid" in data
        assert "total_pending" in data
        assert "total_overdue" in data


@pytest.mark.django_db
class TestAdminCustomerSoftDelete:
    def test_soft_delete_sets_deleted_at(self, admin_client, customer):
        resp = admin_client.delete(f"/api/v1/admin/customers/{customer.id}/delete/")
        assert resp.status_code == 200
        customer.refresh_from_db()
        assert customer.deleted_at is not None

    def test_soft_deleted_customer_excluded_from_list(self, admin_client, customer):
        customer.soft_delete()
        resp = admin_client.get("/api/v1/admin/customers/")
        ids = [c["id"] for c in resp.json()["data"]["results"]]
        assert str(customer.id) not in ids

    def test_soft_delete_already_deleted_returns_400(self, admin_client, customer):
        customer.soft_delete()
        resp = admin_client.delete(f"/api/v1/admin/customers/{customer.id}/delete/")
        assert resp.status_code == 400

    def test_non_admin_cannot_soft_delete(self, customer_client, customer):
        resp = customer_client.delete(f"/api/v1/admin/customers/{customer.id}/delete/")
        assert resp.status_code == 403

    def test_soft_delete_nonexistent_returns_404(self, admin_client):
        resp = admin_client.delete(
            "/api/v1/admin/customers/00000000-0000-0000-0000-000000000000/delete/"
        )
        assert resp.status_code == 404
