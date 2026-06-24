"""Integration tests for the admin MRR dashboard and Invoice soft delete."""

import datetime
from decimal import Decimal

import pytest

from apps.billing.models import Invoice
from apps.customers.models import Customer


def _customer(doc):
    return Customer.objects.create(company_name="MRR Corp", document=doc)


def _invoice(customer, amount, status=Invoice.Status.PAID, days_ago=0):
    from django.utils import timezone

    dt = timezone.now() - datetime.timedelta(days=days_ago)
    inv = Invoice.objects.create(
        customer=customer,
        amount=amount,
        due_date=datetime.date.today(),
        status=status,
    )
    # Force updated_at to simulate it being paid this month
    Invoice.objects.filter(pk=inv.pk).update(updated_at=dt)
    return inv


# ---------------------------------------------------------------------------
# MRR endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAdminMetricsEndpoint:
    def test_admin_can_access_metrics(self, admin_client):
        resp = admin_client.get("/api/v1/admin/metrics/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "mrr" in data
        assert "arr" in data
        assert "active_customers" in data
        assert "new_customers" in data
        assert "churned_customers" in data
        assert "monthly_revenue" in data

    def test_non_admin_cannot_access_metrics(self, customer_client):
        resp = customer_client.get("/api/v1/admin/metrics/")
        assert resp.status_code == 403

    def test_arr_equals_mrr_times_12(self, admin_client):
        customer = _customer("60.000.000/0001-60")
        _invoice(customer, "500.00")
        resp = admin_client.get("/api/v1/admin/metrics/")
        data = resp.json()["data"]
        mrr = Decimal(str(data["mrr"]))
        arr = Decimal(str(data["arr"]))
        assert arr == mrr * 12

    def test_monthly_revenue_is_list(self, admin_client):
        resp = admin_client.get("/api/v1/admin/metrics/")
        assert isinstance(resp.json()["data"]["monthly_revenue"], list)


# ---------------------------------------------------------------------------
# Invoice soft delete
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvoiceSoftDelete:
    def test_soft_delete_sets_deleted_at(self):
        customer = _customer("61.000.000/0001-61")
        inv = _invoice(customer, "100.00")
        assert inv.is_deleted is False
        inv.soft_delete()
        assert inv.is_deleted is True
        assert inv.deleted_at is not None

    def test_soft_deleted_invoice_excluded_from_list_invoices(self):
        from apps.billing.queries import list_invoices

        customer = _customer("62.000.000/0001-62")
        inv1 = _invoice(customer, "200.00")
        inv2 = _invoice(customer, "300.00")
        inv2.soft_delete()

        qs = list_invoices(customer.id, {})
        ids = list(qs.values_list("id", flat=True))
        assert inv1.id in ids
        assert inv2.id not in ids

    def test_soft_deleted_invoice_excluded_from_financial_metrics(self):
        from apps.billing.queries import get_financial_metrics

        customer = _customer("63.000.000/0001-63")
        _invoice(customer, "400.00", status=Invoice.Status.PAID)
        inv_deleted = _invoice(customer, "100.00", status=Invoice.Status.PAID)
        inv_deleted.soft_delete()

        metrics = get_financial_metrics(customer.id)
        assert metrics["total_paid"] == Decimal("400.00")

    def test_soft_deleted_invoice_still_exists_in_db(self):
        customer = _customer("64.000.000/0001-64")
        inv = _invoice(customer, "150.00")
        inv.soft_delete()
        assert Invoice.all_objects.filter(pk=inv.pk).exists()
