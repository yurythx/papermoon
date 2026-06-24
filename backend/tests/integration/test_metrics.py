"""Integration tests for billing metrics endpoints."""

import datetime

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser
from apps.billing.models import Invoice
from apps.customers.models import Customer, CustomerProfile
from apps.licensing.models import LicenseQuota

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_customer(doc: str, status: str = "active") -> Customer:
    return Customer.objects.create(company_name=f"Corp {doc[:4]}", document=doc, status=status)


def _make_invoice(customer: Customer, amount: str, status: str = "pending") -> Invoice:
    return Invoice.objects.create(
        customer=customer,
        amount=amount,
        due_date=datetime.date.today(),
        status=status,
    )


def _make_quota(customer: Customer, used: int = 0, max_calls: int = 10000) -> LicenseQuota:
    return LicenseQuota.objects.create(
        customer=customer,
        max_api_calls=max_calls,
        used_api_calls=used,
        reset_at=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )


def _client_for(email: str, password: str = "pass123") -> APIClient:
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
    return client


# ---------------------------------------------------------------------------
# AdminMRRMetricsView  GET /api/v1/admin/billing/metrics/mrr/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminMRRMetrics:
    def test_returns_mrr_arr_and_customer_counts(self, admin_client):
        customer = _make_customer("10.000.000/0001-10")
        _make_invoice(customer, "500.00", status="paid")
        _make_invoice(customer, "300.00", status="paid")

        resp = admin_client.get("/api/v1/admin/billing/metrics/mrr/")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "mrr" in data
        assert "arr" in data
        assert "active_customers" in data
        assert "monthly_revenue" in data

    def test_arr_is_mrr_times_12(self, admin_client):
        customer = _make_customer("11.000.000/0001-11")
        # Force invoice updated_at to current month by creating it now
        _make_invoice(customer, "100.00", status="paid")

        resp = admin_client.get("/api/v1/admin/billing/metrics/mrr/")
        data = resp.json()["data"]
        assert abs(data["arr"] - data["mrr"] * 12) < 0.01

    def test_non_admin_gets_403(self, customer_client):
        resp = customer_client.get("/api/v1/admin/billing/metrics/mrr/")
        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, api_client):
        resp = api_client.get("/api/v1/admin/billing/metrics/mrr/")
        assert resp.status_code == 401

    def test_monthly_revenue_is_list(self, admin_client):
        resp = admin_client.get("/api/v1/admin/billing/metrics/mrr/")
        data = resp.json()["data"]
        assert isinstance(data["monthly_revenue"], list)

    def test_churned_customers_counted(self, admin_client):
        _make_customer("12.000.000/0001-12", status="cancelled")
        resp = admin_client.get("/api/v1/admin/billing/metrics/mrr/")
        data = resp.json()["data"]
        assert "churned_customers" in data

    def test_revenue_by_plan_groups_by_product(self, admin_client):
        from apps.products.models import Pricing, Product
        from apps.subscriptions.models import Subscription

        customer = _make_customer("13.000.000/0001-13")
        product = Product.objects.create(name="MRR Product", slug="mrr-product")
        pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="400.00")
        sub = Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=datetime.datetime.now(datetime.UTC),
            expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30),
        )
        Invoice.objects.create(
            customer=customer,
            subscription=sub,
            amount="400.00",
            due_date=datetime.date.today(),
            status="paid",
        )

        resp = admin_client.get("/api/v1/admin/billing/metrics/mrr/")
        data = resp.json()["data"]
        plan_row = next((r for r in data["revenue_by_plan"] if r["plan"] == "MRR Product"), None)
        assert plan_row is not None
        assert plan_row["revenue"] == 400.0
        assert plan_row["customer_count"] == 1

    def test_revenue_by_plan_excludes_invoices_without_subscription(self, admin_client):
        customer = _make_customer("14.000.000/0001-14")
        _make_invoice(customer, "999.00", status="paid")

        resp = admin_client.get("/api/v1/admin/billing/metrics/mrr/")
        data = resp.json()["data"]
        assert all(r["plan"] != "Sem plano" for r in data["revenue_by_plan"])


# ---------------------------------------------------------------------------
# AdminAPIUsageMetricsView  GET /api/v1/admin/billing/metrics/api-usage/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminAPIUsageMetrics:
    def test_returns_quota_rows(self, admin_client):
        customer = _make_customer("20.000.000/0001-20")
        _make_quota(customer, used=250, max_calls=1000)

        resp = admin_client.get("/api/v1/admin/billing/metrics/api-usage/")

        assert resp.status_code == 200
        rows = resp.json()["data"]
        assert isinstance(rows, list)
        match = next((r for r in rows if r["customer_id"] == str(customer.id)), None)
        assert match is not None
        assert match["used_api_calls"] == 250
        assert match["max_api_calls"] == 1000

    def test_usage_pct_is_correct(self, admin_client):
        customer = _make_customer("21.000.000/0001-21")
        _make_quota(customer, used=500, max_calls=1000)

        resp = admin_client.get("/api/v1/admin/billing/metrics/api-usage/")
        rows = resp.json()["data"]
        match = next(r for r in rows if r["customer_id"] == str(customer.id))
        assert match["usage_pct"] == 50.0

    def test_filter_by_customer_id(self, admin_client):
        c1 = _make_customer("22.000.000/0001-22")
        c2 = _make_customer("23.000.000/0001-23")
        _make_quota(c1, used=100, max_calls=500)
        _make_quota(c2, used=200, max_calls=500)

        resp = admin_client.get(f"/api/v1/admin/billing/metrics/api-usage/?customer_id={c1.id}")
        rows = resp.json()["data"]
        assert len(rows) == 1
        assert rows[0]["customer_id"] == str(c1.id)

    def test_non_admin_gets_403(self, customer_client):
        resp = customer_client.get("/api/v1/admin/billing/metrics/api-usage/")
        assert resp.status_code == 403

    def test_zero_max_calls_usage_pct_is_zero(self, admin_client):
        customer = _make_customer("24.000.000/0001-24")
        _make_quota(customer, used=0, max_calls=0)

        resp = admin_client.get(
            f"/api/v1/admin/billing/metrics/api-usage/?customer_id={customer.id}"
        )
        rows = resp.json()["data"]
        assert rows[0]["usage_pct"] == 0


# ---------------------------------------------------------------------------
# ClientFinancialMetricsView  GET /api/v1/client/metrics/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestClientFinancialMetrics:
    def _setup(self, doc: str):
        customer = _make_customer(doc)
        user = CustomUser.objects.create_user(
            username=doc[:6], email=f"{doc[:6]}@test.com", password="pass123"
        )
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")
        client = _client_for(f"{doc[:6]}@test.com")
        return client, customer

    def test_returns_financial_totals(self):
        client, customer = self._setup("30.000.000/0001-30")
        _make_invoice(customer, "200.00", status="paid")
        _make_invoice(customer, "100.00", status="pending")
        _make_invoice(customer, "50.00", status="overdue")

        resp = client.get("/api/v1/client/metrics/")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_paid"] == 200.0
        assert data["total_pending"] == 100.0
        assert data["total_overdue"] == 50.0

    def test_does_not_include_other_customers_invoices(self):
        client, my_customer = self._setup("31.000.000/0001-31")
        other = _make_customer("32.000.000/0001-32")
        _make_invoice(my_customer, "100.00", status="paid")
        _make_invoice(other, "9999.00", status="paid")

        resp = client.get("/api/v1/client/metrics/")
        data = resp.json()["data"]
        assert data["total_paid"] == 100.0

    def test_excludes_soft_deleted_invoices(self):
        from django.utils import timezone

        client, customer = self._setup("33.000.000/0001-33")
        inv = _make_invoice(customer, "500.00", status="paid")
        inv.deleted_at = timezone.now()
        inv.save()

        resp = client.get("/api/v1/client/metrics/")
        data = resp.json()["data"]
        assert data["total_paid"] == 0.0

    def test_unauthenticated_gets_401(self, api_client):
        resp = api_client.get("/api/v1/client/metrics/")
        assert resp.status_code == 401

    def test_zeros_when_no_invoices(self):
        client, _ = self._setup("34.000.000/0001-34")
        resp = client.get("/api/v1/client/metrics/")
        data = resp.json()["data"]
        assert data["total_paid"] == 0.0
        assert data["total_pending"] == 0.0
        assert data["total_overdue"] == 0.0
