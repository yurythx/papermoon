import datetime

import pytest

from apps.billing.models import Invoice
from apps.customers.models import Customer


def _make_customer():
    return Customer.objects.create(
        company_name="Billing Corp",
        document="55.555.555/0001-55",
    )


def _make_invoice(customer, status=Invoice.Status.PENDING):
    return Invoice.objects.create(
        customer=customer,
        amount="300.00",
        due_date=datetime.date.today(),
        status=status,
    )


@pytest.mark.django_db
class TestAsaasWebhook:
    WEBHOOK_URL = "/api/v1/webhooks/asaas/"
    VALID_TOKEN = "test-webhook-token"

    @pytest.fixture(autouse=True)
    def patch_token(self, settings):
        settings.ASAAS_WEBHOOK_TOKEN = self.VALID_TOKEN

    def _payload(self, event, asaas_id="asaas-123"):
        return {"event": event, "payment": {"id": asaas_id}}

    def test_missing_token_returns_403(self, api_client, customer):
        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-123"
        invoice.save()
        resp = api_client.post(self.WEBHOOK_URL, self._payload("PAYMENT_RECEIVED"), format="json")
        assert resp.status_code == 403

    def test_wrong_token_returns_403(self, api_client, customer):
        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-123"
        invoice.save()
        resp = api_client.post(
            self.WEBHOOK_URL,
            self._payload("PAYMENT_RECEIVED"),
            format="json",
            HTTP_ASAAS_ACCESS_TOKEN="wrong-token",
        )
        assert resp.status_code == 403

    def test_payment_received_enqueues_celery_task(self, api_client, customer):
        from unittest.mock import patch

        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-999"
        invoice.save()

        with patch("apps.billing.views.handle_asaas_payment_received.delay") as mock_task:
            resp = api_client.post(
                self.WEBHOOK_URL,
                {"event": "PAYMENT_RECEIVED", "payment": {"id": "asaas-999"}},
                format="json",
                HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN,
            )
            assert resp.status_code == 200
            mock_task.assert_called_once_with(str(invoice.id))

    def test_payment_overdue_enqueues_celery_task(self, api_client, customer):
        from unittest.mock import patch

        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-overdue"
        invoice.save()

        with patch("apps.billing.views.handle_asaas_payment_overdue.delay") as mock_task:
            api_client.post(
                self.WEBHOOK_URL,
                {"event": "PAYMENT_OVERDUE", "payment": {"id": "asaas-overdue"}},
                format="json",
                HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN,
            )
            mock_task.assert_called_once_with(str(invoice.id))

    def test_webhook_returns_200_immediately(self, api_client, customer):
        from unittest.mock import patch

        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-fast"
        invoice.save()

        with patch("apps.billing.views.handle_asaas_payment_received.delay"):
            resp = api_client.post(
                self.WEBHOOK_URL,
                {"event": "PAYMENT_RECEIVED", "payment": {"id": "asaas-fast"}},
                format="json",
                HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN,
            )
        assert resp.status_code == 200
        assert resp.json()["data"]["received"] is True
        # Invoice is still pending — processing is async
        invoice.refresh_from_db()
        assert invoice.status == Invoice.Status.PENDING

    def test_unknown_event_type_returns_200_noop(self, api_client, customer):
        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-unknown"
        invoice.save()

        resp = api_client.post(
            self.WEBHOOK_URL,
            {"event": "PAYMENT_REFUNDED", "payment": {"id": "asaas-unknown"}},
            format="json",
            HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN,
        )
        assert resp.status_code == 200

    def test_duplicate_webhook_id_is_skipped(self, api_client, customer):
        from unittest.mock import patch

        from apps.billing.models import WebhookEvent

        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-dup"
        invoice.save()
        payload = {
            "id": "evt-dup-1",
            "event": "PAYMENT_RECEIVED",
            "payment": {"id": "asaas-dup"},
        }

        with patch("apps.billing.views.handle_asaas_payment_received.delay") as mock_task:
            first = api_client.post(
                self.WEBHOOK_URL, payload, format="json", HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN
            )
            second = api_client.post(
                self.WEBHOOK_URL, payload, format="json", HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN
            )

        assert first.status_code == 200
        assert second.status_code == 200
        assert WebhookEvent.objects.filter(asaas_event_id="evt-dup-1").count() == 1
        mock_task.assert_called_once_with(str(invoice.id))

    def test_distinct_webhook_ids_both_processed(self, api_client, customer):
        from unittest.mock import patch

        invoice = _make_invoice(customer)
        invoice.asaas_id = "asaas-distinct"
        invoice.save()

        with patch("apps.billing.views.handle_asaas_payment_received.delay") as mock_task:
            api_client.post(
                self.WEBHOOK_URL,
                {"id": "evt-1", "event": "PAYMENT_RECEIVED", "payment": {"id": "asaas-distinct"}},
                format="json",
                HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN,
            )
            api_client.post(
                self.WEBHOOK_URL,
                {"id": "evt-2", "event": "PAYMENT_RECEIVED", "payment": {"id": "asaas-distinct"}},
                format="json",
                HTTP_ASAAS_ACCESS_TOKEN=self.VALID_TOKEN,
            )

        assert mock_task.call_count == 2


@pytest.mark.django_db
class TestRegisterChargeTask:
    def test_skipped_when_asaas_api_key_not_configured(self, settings):
        from unittest.mock import patch

        from apps.billing.tasks import register_charge_task

        settings.ASAAS_API_KEY = ""
        customer = _make_customer()
        invoice = _make_invoice(customer)

        with patch("apps.billing.commands.RegisterChargeCommand") as mock_command:
            register_charge_task(str(invoice.id), "BOLETO")

        mock_command.assert_not_called()

    def test_dispatches_to_gateway_when_configured(self, settings):
        from unittest.mock import patch

        from apps.billing.tasks import register_charge_task

        settings.ASAAS_API_KEY = "fake-key"
        customer = _make_customer()
        invoice = _make_invoice(customer)

        with (
            patch("apps.billing.gateway.asaas_adapter.AsaasGateway"),
            patch("apps.billing.commands.RegisterChargeCommand") as mock_command,
        ):
            register_charge_task(str(invoice.id), "PIX")

        mock_command.assert_called_once()
        mock_command.return_value.execute.assert_called_once()

    def test_retries_on_gateway_failure(self, settings):
        from unittest.mock import patch

        from celery.exceptions import Retry

        from apps.billing.tasks import register_charge_task

        settings.ASAAS_API_KEY = "fake-key"
        customer = _make_customer()
        invoice = _make_invoice(customer)

        with (
            patch("apps.billing.gateway.asaas_adapter.AsaasGateway"),
            patch(
                "apps.billing.commands.RegisterChargeCommand.execute",
                side_effect=RuntimeError("gateway down"),
            ),
            pytest.raises((Retry, RuntimeError)),
        ):
            register_charge_task(str(invoice.id), "BOLETO")


@pytest.mark.django_db
class TestScanOverdueInvoicesTask:
    def test_scan_marks_pending_past_due_as_overdue(self):
        from apps.billing.tasks import scan_overdue_invoices

        customer = _make_customer()
        invoice = Invoice.objects.create(
            customer=customer,
            amount="100.00",
            due_date=datetime.date(2000, 1, 1),  # well in the past
            status=Invoice.Status.PENDING,
        )

        scan_overdue_invoices()

        invoice.refresh_from_db()
        assert invoice.status == Invoice.Status.OVERDUE

    def test_scan_skips_already_paid_invoices(self):
        from apps.billing.tasks import scan_overdue_invoices

        customer = _make_customer()
        invoice = Invoice.objects.create(
            customer=customer,
            amount="100.00",
            due_date=datetime.date(2000, 1, 1),
            status=Invoice.Status.PAID,
        )

        scan_overdue_invoices()

        invoice.refresh_from_db()
        assert invoice.status == Invoice.Status.PAID


@pytest.mark.django_db
class TestBillingQueries:
    def test_get_financial_metrics_returns_correct_totals(self):
        from apps.billing.queries import get_financial_metrics

        customer = _make_customer()
        Invoice.objects.create(
            customer=customer,
            amount="500.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PAID,
        )
        Invoice.objects.create(
            customer=customer,
            amount="200.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PENDING,
        )
        Invoice.objects.create(
            customer=customer,
            amount="100.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.OVERDUE,
        )

        metrics = get_financial_metrics(customer.id)

        assert metrics["total_paid"] == 500
        assert metrics["total_pending"] == 200
        assert metrics["total_overdue"] == 100

    def test_list_invoices_filters_by_status(self):
        from apps.billing.queries import list_invoices

        customer = _make_customer()
        Invoice.objects.create(
            customer=customer,
            amount="100.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PAID,
        )
        Invoice.objects.create(
            customer=customer,
            amount="200.00",
            due_date=datetime.date.today(),
            status=Invoice.Status.PENDING,
        )

        qs = list_invoices(customer.id, {"status": Invoice.Status.PAID})

        assert qs.count() == 1
        assert qs.first().status == Invoice.Status.PAID


@pytest.mark.django_db
class TestAdminInvoiceList:
    BASE_URL = "/api/v1/admin/billing/invoices/"

    def _admin_client(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        user = CustomUser.objects.create_superuser(
            username="listadmin",
            email="listadmin@papermoon.com",
            password="pass1234",
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": "listadmin@papermoon.com", "password": "pass1234"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        return client

    def test_admin_lists_all_invoices(self):
        customer = _make_customer()
        _make_invoice(customer, Invoice.Status.PAID)
        _make_invoice(customer, Invoice.Status.OVERDUE)
        client = self._admin_client()
        resp = client.get(self.BASE_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["count"] >= 2
        assert "results" in data
        assert "company_name" in data["results"][0]

    def test_admin_filters_by_status(self):
        customer = _make_customer()
        _make_invoice(customer, Invoice.Status.PAID)
        _make_invoice(customer, Invoice.Status.OVERDUE)
        client = self._admin_client()
        resp = client.get(self.BASE_URL, {"status": "paid"})
        assert resp.status_code == 200
        results = resp.json()["data"]["results"]
        assert all(r["status"] == "paid" for r in results)

    def test_admin_list_hides_untrusted_payment_url(self):
        customer = _make_customer()
        invoice = _make_invoice(customer, Invoice.Status.PENDING)
        invoice.payment_url = "https://evil.example.com/pay-123"
        invoice.save(update_fields=["payment_url"])
        client = self._admin_client()

        resp = client.get(self.BASE_URL)

        assert resp.status_code == 200
        result = next(item for item in resp.json()["data"]["results"] if item["id"] == str(invoice.id))
        assert result["payment_url"] is None

    def test_soft_deleted_invoice_excluded_from_list(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)
        invoice.soft_delete()
        client = self._admin_client()
        resp = client.get(self.BASE_URL)
        ids = [r["id"] for r in resp.json()["data"]["results"]]
        assert str(invoice.id) not in ids

    def test_admin_filters_by_invoice_type(self):
        customer = _make_customer()
        Invoice.objects.create(
            customer=customer,
            amount="100.00",
            due_date=datetime.date.today(),
            invoice_type=Invoice.Type.SUPPORT,
        )
        Invoice.objects.create(
            customer=customer,
            amount="200.00",
            due_date=datetime.date.today(),
            invoice_type=Invoice.Type.IMPLEMENTATION,
        )
        client = self._admin_client()
        resp = client.get(self.BASE_URL, {"invoice_type": "support"})
        assert resp.status_code == 200
        results = resp.json()["data"]["results"]
        assert all(r["invoice_type"] == "support" for r in results)

    def test_admin_filters_by_customer_id(self):
        customer_a = _make_customer()
        customer_b = Customer.objects.create(
            company_name="Other Corp", document="56.555.555/0001-56"
        )
        _make_invoice(customer_a)
        _make_invoice(customer_b)
        client = self._admin_client()
        resp = client.get(self.BASE_URL, {"customer_id": str(customer_a.id)})
        assert resp.status_code == 200
        results = resp.json()["data"]["results"]
        assert all(r["customer_id"] == str(customer_a.id) for r in results)

    def test_invalid_page_param_falls_back_to_page_1(self):
        customer = _make_customer()
        _make_invoice(customer)
        client = self._admin_client()
        resp = client.get(self.BASE_URL, {"page": "not-a-number"})
        assert resp.status_code == 200
        assert resp.json()["data"]["page"] == 1

    def test_non_admin_cannot_list_invoices(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        user = CustomUser.objects.create_user(
            username="normaluser2", email="normaluser2@papermoon.com", password="pass1234"
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": "normaluser2@papermoon.com", "password": "pass1234"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        resp = client.get(self.BASE_URL)
        assert resp.status_code == 403


@pytest.mark.django_db
class TestAdminInvoiceCreate:
    BASE_URL = "/api/v1/admin/billing/invoices/"

    def _admin_client(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        user = CustomUser.objects.create_superuser(
            username="createadmin",
            email="createadmin@papermoon.com",
            password="pass1234",
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": "createadmin@papermoon.com", "password": "pass1234"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        return client

    def test_creates_avulsa_invoice_and_dispatches_charge(self):
        from unittest.mock import patch

        customer = _make_customer()
        client = self._admin_client()

        with patch("apps.billing.tasks.register_charge_task.delay") as mock_task:
            resp = client.post(
                self.BASE_URL,
                {
                    "customer_id": str(customer.id),
                    "amount": "150.00",
                    "due_date": str(datetime.date.today()),
                    "invoice_type": Invoice.Type.SUPPORT,
                    "description": "Suporte extra",
                },
                format="json",
            )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["customer_id"] == str(customer.id)
        assert data["invoice_type"] == "support"
        assert data["amount"] == "150.00"
        invoice = Invoice.objects.get(pk=data["id"])
        mock_task.assert_called_once_with(str(invoice.id), "BOLETO")

    def test_missing_required_fields_returns_400(self):
        client = self._admin_client()
        resp = client.post(self.BASE_URL, {}, format="json")
        assert resp.status_code == 400

    def test_invalid_invoice_type_returns_400(self):
        customer = _make_customer()
        client = self._admin_client()
        resp = client.post(
            self.BASE_URL,
            {
                "customer_id": str(customer.id),
                "amount": "100.00",
                "due_date": str(datetime.date.today()),
                "invoice_type": "not_a_real_type",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_nonexistent_customer_returns_404(self):
        client = self._admin_client()
        resp = client.post(
            self.BASE_URL,
            {
                "customer_id": "00000000-0000-0000-0000-000000000000",
                "amount": "100.00",
                "due_date": str(datetime.date.today()),
            },
            format="json",
        )
        assert resp.status_code == 404

    def test_invalid_billing_type_falls_back_to_boleto(self):
        from unittest.mock import patch

        customer = _make_customer()
        client = self._admin_client()

        with patch("apps.billing.tasks.register_charge_task.delay") as mock_task:
            resp = client.post(
                self.BASE_URL,
                {
                    "customer_id": str(customer.id),
                    "amount": "100.00",
                    "due_date": str(datetime.date.today()),
                    "billing_type": "not_a_real_method",
                },
                format="json",
            )

        assert resp.status_code == 201
        assert resp.json()["data"]["billing_type"] == "BOLETO"
        mock_task.assert_called_once()

    def test_create_failure_returns_500(self):
        from unittest.mock import patch

        customer = _make_customer()
        client = self._admin_client()

        with patch("apps.billing.models.Invoice.objects.create", side_effect=RuntimeError("boom")):
            resp = client.post(
                self.BASE_URL,
                {
                    "customer_id": str(customer.id),
                    "amount": "100.00",
                    "due_date": str(datetime.date.today()),
                },
                format="json",
            )

        assert resp.status_code == 500

    def test_non_admin_cannot_create_invoice(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        customer = _make_customer()
        user = CustomUser.objects.create_user(
            username="normaluser3", email="normaluser3@papermoon.com", password="pass1234"
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": "normaluser3@papermoon.com", "password": "pass1234"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        resp = client.post(
            self.BASE_URL,
            {
                "customer_id": str(customer.id),
                "amount": "100.00",
                "due_date": str(datetime.date.today()),
            },
            format="json",
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestAdminInvoiceSoftDelete:
    BASE_URL = "/api/v1/admin/billing/invoices/"

    def _admin_client(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser

        user = CustomUser.objects.create_superuser(
            username="billingadmin",
            email="billingadmin@papermoon.com",
            password="pass1234",
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": "billingadmin@papermoon.com", "password": "pass1234"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")
        return client

    def test_soft_delete_invoice_sets_deleted_at(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)
        client = self._admin_client()
        resp = client.delete(f"{self.BASE_URL}{invoice.id}/")
        assert resp.status_code == 200
        invoice.refresh_from_db()
        assert invoice.deleted_at is not None

    def test_soft_deleted_invoice_not_in_client_list(self):
        from rest_framework.test import APIClient

        from apps.accounts.models import CustomUser
        from apps.customers.models import CustomerProfile

        customer = _make_customer()
        invoice = _make_invoice(customer)
        invoice.soft_delete()

        user = CustomUser.objects.create_user(
            username="clientuser", email="clientuser@papermoon.com", password="pass1234"
        )
        CustomerProfile.objects.create(
            user=user, customer=customer, role=CustomerProfile.Role.OWNER
        )
        client = APIClient()
        resp = client.post(
            "/api/v1/auth/login/",
            {"email": "clientuser@papermoon.com", "password": "pass1234"},
            format="json",
        )
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['data']['access']}")

        resp = client.get("/api/v1/client/invoices/")
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["data"]["results"]]
        assert str(invoice.id) not in ids

    def test_soft_delete_already_deleted_invoice_returns_400(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)
        invoice.soft_delete()
        client = self._admin_client()
        resp = client.delete(f"{self.BASE_URL}{invoice.id}/")
        assert resp.status_code == 400

    def test_soft_delete_nonexistent_invoice_returns_404(self):
        client = self._admin_client()
        resp = client.delete(f"{self.BASE_URL}00000000-0000-0000-0000-000000000000/")
        assert resp.status_code == 404
