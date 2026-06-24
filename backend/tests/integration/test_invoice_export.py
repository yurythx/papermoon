"""
Integration tests for GET /api/v1/client/invoices/export/
CSV download endpoint.
"""

import datetime

import pytest

from apps.billing.models import Invoice
from apps.customers.models import Customer, CustomerProfile

URL = "/api/v1/client/invoices/export/"


def _make_customer_with_client(email: str, doc: str):
    from rest_framework.test import APIClient

    from apps.accounts.models import CustomUser

    user = CustomUser.objects.create_user(username=email, email=email, password="pass1234")
    customer = Customer.objects.create(company_name="CSV Corp", document=doc)
    CustomerProfile.objects.create(user=user, customer=customer, role="owner")

    client = APIClient()
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": "pass1234"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
    return client, customer


def _invoice(customer, status=Invoice.Status.PAID, amount="199.00", offset_days=0):
    return Invoice.objects.create(
        customer=customer,
        amount=amount,
        due_date=datetime.date.today() - datetime.timedelta(days=offset_days),
        status=status,
    )


@pytest.mark.django_db
class TestInvoiceExportCSV:
    def test_returns_200_with_csv_content_type(self):
        client, customer = _make_customer_with_client("csv1@test.com", "10.000.000/0001-10")
        _invoice(customer)
        resp = client.get(URL)
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]

    def test_content_disposition_attachment(self):
        client, customer = _make_customer_with_client("csv2@test.com", "20.000.000/0001-20")
        _invoice(customer)
        resp = client.get(URL)
        assert "attachment" in resp["Content-Disposition"]
        assert "faturas.csv" in resp["Content-Disposition"]

    def test_csv_has_header_row(self):
        client, customer = _make_customer_with_client("csv3@test.com", "30.000.000/0001-30")
        resp = client.get(URL)
        content = resp.content.decode()
        assert "ID" in content
        assert "Status" in content
        assert "Valor" in content
        assert "Vencimento" in content

    def test_csv_contains_invoice_data(self):
        client, customer = _make_customer_with_client("csv4@test.com", "40.000.000/0001-40")
        inv = _invoice(customer, amount="350.00")
        resp = client.get(URL)
        content = resp.content.decode()
        assert str(inv.id)[:8] in content
        assert "350.00" in content
        assert "paid" in content

    def test_multiple_invoices_all_appear(self):
        client, customer = _make_customer_with_client("csv5@test.com", "50.000.000/0001-50")
        _invoice(customer, offset_days=30)
        _invoice(customer, offset_days=60)
        _invoice(customer, status=Invoice.Status.PENDING)
        resp = client.get(URL)
        lines = resp.content.decode().strip().split("\n")
        # header + 3 invoices
        assert len(lines) == 4

    def test_status_filter_limits_rows(self):
        client, customer = _make_customer_with_client("csv6@test.com", "60.000.000/0001-60")
        _invoice(customer, status=Invoice.Status.PAID)
        _invoice(customer, status=Invoice.Status.PENDING)
        _invoice(customer, status=Invoice.Status.OVERDUE)
        resp = client.get(URL + "?status=paid")
        lines = resp.content.decode().strip().split("\n")
        assert len(lines) == 2  # header + 1

    def test_unauthenticated_returns_401(self):
        from rest_framework.test import APIClient

        anon = APIClient()
        resp = anon.get(URL)
        assert resp.status_code == 401

    def test_empty_returns_header_only(self):
        client, _ = _make_customer_with_client("csv7@test.com", "70.000.000/0001-70")
        resp = client.get(URL)
        content = resp.content.decode().strip()
        lines = content.split("\n")
        # Only header, no data rows
        assert len(lines) == 1
        assert "ID" in lines[0]

    def test_isolates_to_own_customer(self):
        client, customer = _make_customer_with_client("csv8@test.com", "80.000.000/0001-80")
        other = Customer.objects.create(company_name="Other", document="81.000.000/0001-81")
        # Invoice belonging to other customer
        _invoice(other, amount="999.00")
        # Invoice belonging to our customer
        _invoice(customer, amount="100.00")
        resp = client.get(URL)
        content = resp.content.decode()
        assert "999.00" not in content
        assert "100.00" in content
