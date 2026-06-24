import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.billing.commands import (
    ConfirmPaymentCommand,
    CreateManualInvoiceCommand,
    MarkOverdueCommand,
    RegisterChargeCommand,
)
from apps.billing.models import Invoice
from apps.billing.repositories import DjangoInvoiceRepository
from apps.customers.models import Customer


def _make_customer():
    return Customer.objects.create(
        company_name="Billing Teste",
        document="22.222.222/0001-22",
    )


def _make_invoice(customer, status=Invoice.Status.PENDING, asaas_id=""):
    return Invoice.objects.create(
        customer=customer,
        amount="200.00",
        due_date=datetime.date.today(),
        status=status,
        asaas_id=asaas_id,
    )


# ---------------------------------------------------------------------------
# MarkOverdueCommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMarkOverdueCommand:
    def test_marks_invoice_as_overdue(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)

        result = MarkOverdueCommand(invoice.id).execute()

        assert result.status == Invoice.Status.OVERDUE

    def test_creates_payment_failed_outbox_event(self):
        from shared.models import OutboxEvent

        customer = _make_customer()
        invoice = _make_invoice(customer)

        MarkOverdueCommand(invoice.id).execute()

        event = OutboxEvent.objects.get(event_type="payment.failed")
        assert event.payload["invoice_id"] == str(invoice.id)
        assert event.payload["customer_id"] == str(customer.id)

    def test_idempotent_on_already_overdue(self):
        from shared.models import OutboxEvent

        customer = _make_customer()
        invoice = _make_invoice(customer, status=Invoice.Status.OVERDUE)

        MarkOverdueCommand(invoice.id).execute()

        assert not OutboxEvent.objects.filter(event_type="payment.failed").exists()

    def test_raises_not_found_for_missing_invoice(self):
        from rest_framework.exceptions import NotFound

        with pytest.raises(NotFound):
            MarkOverdueCommand(uuid4()).execute()


# ---------------------------------------------------------------------------
# ConfirmPaymentCommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestConfirmPaymentCommand:
    def test_marks_invoice_as_paid(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)

        result = ConfirmPaymentCommand(invoice.id).execute()

        assert result.status == Invoice.Status.PAID

    def test_creates_payment_processed_outbox_event(self):
        from shared.models import OutboxEvent

        customer = _make_customer()
        invoice = _make_invoice(customer)

        ConfirmPaymentCommand(invoice.id).execute()

        event = OutboxEvent.objects.get(event_type="payment.processed")
        assert event.payload["invoice_id"] == str(invoice.id)

    def test_idempotent_on_already_paid(self):
        from shared.models import OutboxEvent

        customer = _make_customer()
        invoice = _make_invoice(customer, status=Invoice.Status.PAID)

        ConfirmPaymentCommand(invoice.id).execute()

        assert not OutboxEvent.objects.filter(event_type="payment.processed").exists()

    def test_raises_not_found_for_missing_invoice(self):
        from rest_framework.exceptions import NotFound

        with pytest.raises(NotFound):
            ConfirmPaymentCommand(uuid4()).execute()


# ---------------------------------------------------------------------------
# RegisterChargeCommand
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRegisterChargeCommand:
    def test_sets_asaas_id_and_creates_outbox_event(self):
        from shared.models import OutboxEvent

        customer = _make_customer()
        invoice = _make_invoice(customer)

        gateway = MagicMock()
        gateway.create_charge.return_value = {"id": "asaas-abc-123"}

        result = RegisterChargeCommand(invoice.id, gateway).execute()

        assert result.asaas_id == "asaas-abc-123"
        event = OutboxEvent.objects.get(event_type="charge.registered")
        assert event.payload["asaas_id"] == "asaas-abc-123"

    def test_idempotent_when_asaas_id_already_set(self):
        from shared.models import OutboxEvent

        customer = _make_customer()
        invoice = _make_invoice(customer, asaas_id="already-set")

        gateway = MagicMock()
        result = RegisterChargeCommand(invoice.id, gateway).execute()

        gateway.create_charge.assert_not_called()
        assert result.asaas_id == "already-set"
        assert not OutboxEvent.objects.exists()

    def test_http_called_outside_transaction(self):
        """Gateway.create_charge must be called before transaction.atomic block."""
        customer = _make_customer()
        invoice = _make_invoice(customer)

        call_order = []
        gateway = MagicMock()
        gateway.create_charge.side_effect = lambda *a, **kw: call_order.append("http") or {
            "id": "x"
        }

        original_atomic = __import__("django.db", fromlist=["transaction"]).transaction.atomic

        def tracked_atomic(*args, **kwargs):
            call_order.append("atomic_start")
            return original_atomic(*args, **kwargs)

        with patch("apps.billing.commands.transaction.atomic", side_effect=tracked_atomic):
            RegisterChargeCommand(invoice.id, gateway).execute()

        assert call_order[0] == "http", "HTTP must fire before the atomic block"

    def test_saves_payment_url_from_asaas_invoice_url(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)

        gateway = MagicMock()
        gateway.create_charge.return_value = {
            "id": "asaas-xyz",
            "invoiceUrl": "https://www.asaas.com/c/asaas-xyz",
        }

        result = RegisterChargeCommand(invoice.id, gateway).execute()

        assert result.payment_url == "https://www.asaas.com/c/asaas-xyz"
        result.refresh_from_db()
        assert result.payment_url == "https://www.asaas.com/c/asaas-xyz"

    def test_falls_back_to_bank_slip_url_when_no_invoice_url(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)

        gateway = MagicMock()
        gateway.create_charge.return_value = {
            "id": "asaas-boleto",
            "bankSlipUrl": "https://www.asaas.com/b/pdf/asaas-boleto",
        }

        result = RegisterChargeCommand(invoice.id, gateway).execute()

        assert result.payment_url == "https://www.asaas.com/b/pdf/asaas-boleto"

    def test_payment_url_empty_when_asaas_returns_none(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)

        gateway = MagicMock()
        gateway.create_charge.return_value = {"id": "asaas-pix"}

        result = RegisterChargeCommand(invoice.id, gateway).execute()

        assert result.payment_url == ""

    def test_payment_url_empty_when_gateway_returns_untrusted_domain(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)

        gateway = MagicMock()
        gateway.create_charge.return_value = {
            "id": "asaas-phishing",
            "invoiceUrl": "https://evil.example.com/pay/asaas-phishing",
        }

        result = RegisterChargeCommand(invoice.id, gateway).execute()

        assert result.payment_url == ""


# ---------------------------------------------------------------------------
# CreateManualInvoiceCommand (unit — repositories mocked)
# ---------------------------------------------------------------------------


class TestCreateManualInvoiceCommand:
    def _make_command(self):
        self.invoice_repo = MagicMock()
        self.customer_repo = MagicMock()
        return CreateManualInvoiceCommand(
            invoice_repository=self.invoice_repo,
            customer_repository=self.customer_repo,
        )

    def test_resolves_customer_via_repository(self):
        from uuid import UUID

        cmd = self._make_command()
        customer_id = str(uuid4())
        fake_customer = MagicMock(id=customer_id)
        fake_invoice = MagicMock(id=uuid4())
        self.customer_repo.get_by_id.return_value = fake_customer
        self.invoice_repo.create.return_value = fake_invoice

        with patch("apps.billing.tasks.register_charge_task") as mock_task:
            mock_task.delay = MagicMock()
            cmd.execute(
                customer_id=customer_id,
                invoice_type="support",
                billing_type="BOLETO",
                amount="500.00",
                due_date=datetime.date.today(),
            )

        self.customer_repo.get_by_id.assert_called_once_with(UUID(customer_id))

    def test_creates_invoice_via_repository(self):
        cmd = self._make_command()
        customer_id = str(uuid4())
        fake_customer = MagicMock()
        fake_invoice = MagicMock(id=uuid4())
        self.customer_repo.get_by_id.return_value = fake_customer
        self.invoice_repo.create.return_value = fake_invoice
        due = datetime.date(2026, 12, 31)

        with patch("apps.billing.tasks.register_charge_task") as mock_task:
            mock_task.delay = MagicMock()
            cmd.execute(
                customer_id=customer_id,
                invoice_type="implementation",
                billing_type="PIX",
                amount="1500.00",
                due_date=due,
                description="Projeto X",
            )

        self.invoice_repo.create.assert_called_once_with(
            {
                "customer": fake_customer,
                "invoice_type": "implementation",
                "billing_type": "PIX",
                "description": "Projeto X",
                "amount": "1500.00",
                "due_date": due,
            }
        )

    def test_dispatches_register_charge_task(self):
        cmd = self._make_command()
        fake_invoice = MagicMock(id=uuid4())
        self.customer_repo.get_by_id.return_value = MagicMock()
        self.invoice_repo.create.return_value = fake_invoice

        with patch("apps.billing.tasks.register_charge_task") as mock_task:
            mock_task.delay = MagicMock()
            cmd.execute(
                customer_id=str(uuid4()),
                invoice_type="support",
                billing_type="BOLETO",
                amount="200.00",
                due_date=datetime.date.today(),
            )

        mock_task.delay.assert_called_once_with(str(fake_invoice.id), "BOLETO")

    def test_propagates_not_found_from_customer_repo(self):
        from rest_framework.exceptions import NotFound

        cmd = self._make_command()
        self.customer_repo.get_by_id.side_effect = NotFound("Customer not found")

        with pytest.raises(NotFound):
            cmd.execute(
                customer_id=str(uuid4()),
                invoice_type="support",
                billing_type="BOLETO",
                amount="100.00",
                due_date=datetime.date.today(),
            )

        self.invoice_repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# DjangoInvoiceRepository
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDjangoInvoiceRepository:
    def test_create_persists_invoice(self):
        customer = _make_customer()
        repo = DjangoInvoiceRepository()

        invoice = repo.create(
            {
                "customer": customer,
                "invoice_type": Invoice.Type.SUPPORT,
                "billing_type": Invoice.BillingType.BOLETO,
                "description": "Teste repo",
                "amount": "350.00",
                "due_date": datetime.date.today(),
            }
        )

        assert invoice.pk is not None
        assert Invoice.objects.filter(pk=invoice.pk).exists()
        assert str(invoice.amount) == "350.00"

    def test_get_by_id_returns_invoice(self):
        customer = _make_customer()
        invoice = _make_invoice(customer)
        repo = DjangoInvoiceRepository()

        found = repo.get_by_id(invoice.id)

        assert found.id == invoice.id

    def test_get_by_id_raises_not_found_for_missing_id(self):
        from rest_framework.exceptions import NotFound

        repo = DjangoInvoiceRepository()

        with pytest.raises(NotFound):
            repo.get_by_id(uuid4())
