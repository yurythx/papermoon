"""Unit tests for apps/billing/tasks.py.

Celery tasks are called directly (no broker) with commands mocked.
"""

import datetime
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# handle_asaas_payment_received
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_handle_asaas_payment_received_calls_confirm_command(invoice):
    from apps.billing.tasks import handle_asaas_payment_received

    with patch("apps.billing.commands.ConfirmPaymentCommand.execute") as mock_exec:
        handle_asaas_payment_received(str(invoice.id))
        mock_exec.assert_called_once()


@pytest.mark.django_db
def test_handle_asaas_payment_received_retries_on_exception(invoice):
    from celery.exceptions import Retry

    from apps.billing.tasks import handle_asaas_payment_received

    with patch(
        "apps.billing.commands.ConfirmPaymentCommand.execute",
        side_effect=RuntimeError("db error"),
    ):
        with pytest.raises((Retry, RuntimeError)):
            handle_asaas_payment_received(str(invoice.id))


# ---------------------------------------------------------------------------
# handle_asaas_payment_overdue
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_handle_asaas_payment_overdue_calls_mark_overdue_command(invoice):
    from apps.billing.tasks import handle_asaas_payment_overdue

    with patch("apps.billing.commands.MarkOverdueCommand.execute") as mock_exec:
        handle_asaas_payment_overdue(str(invoice.id))
        mock_exec.assert_called_once()


@pytest.mark.django_db
def test_handle_asaas_payment_overdue_retries_on_exception(invoice):
    from celery.exceptions import Retry

    from apps.billing.tasks import handle_asaas_payment_overdue

    with patch(
        "apps.billing.commands.MarkOverdueCommand.execute",
        side_effect=ValueError("bad state"),
    ):
        with pytest.raises((Retry, ValueError)):
            handle_asaas_payment_overdue(str(invoice.id))


# ---------------------------------------------------------------------------
# scan_overdue_invoices
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_scan_overdue_invoices_marks_past_due_invoice(customer):
    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_overdue_invoices

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    inv = Invoice.objects.create(
        customer=customer,
        amount="100.00",
        due_date=yesterday,
        status=Invoice.Status.PENDING,
    )

    scan_overdue_invoices()

    inv.refresh_from_db()
    assert inv.status == Invoice.Status.OVERDUE


@pytest.mark.django_db
def test_scan_overdue_invoices_skips_already_overdue(customer):
    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_overdue_invoices

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    inv = Invoice.objects.create(
        customer=customer,
        amount="100.00",
        due_date=yesterday,
        status=Invoice.Status.OVERDUE,
    )

    with patch("apps.billing.commands.MarkOverdueCommand.execute") as mock_exec:
        scan_overdue_invoices()
        mock_exec.assert_not_called()


@pytest.mark.django_db
def test_scan_overdue_invoices_skips_future_invoice(customer):
    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_overdue_invoices

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    inv = Invoice.objects.create(
        customer=customer,
        amount="100.00",
        due_date=tomorrow,
        status=Invoice.Status.PENDING,
    )

    scan_overdue_invoices()

    inv.refresh_from_db()
    assert inv.status == Invoice.Status.PENDING


@pytest.mark.django_db
def test_scan_overdue_invoices_logs_error_and_continues(customer):
    """A single failing invoice must not abort the rest of the batch."""

    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_overdue_invoices

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    inv1 = Invoice.objects.create(
        customer=customer,
        amount="100.00",
        due_date=yesterday,
        status=Invoice.Status.PENDING,
    )
    inv2 = Invoice.objects.create(
        customer=customer,
        amount="200.00",
        due_date=yesterday,
        status=Invoice.Status.PENDING,
    )

    call_count = 0

    def side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("transient error on first invoice")

    with patch("apps.billing.commands.MarkOverdueCommand.execute", side_effect=side_effect):
        scan_overdue_invoices()

    assert call_count == 2


# ---------------------------------------------------------------------------
# scan_upcoming_invoices
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_scan_upcoming_invoices_creates_outbox_event(customer):
    import datetime

    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_upcoming_invoices
    from shared.models import OutboxEvent

    due_date = datetime.date.today() + datetime.timedelta(days=3)
    inv = Invoice.objects.create(
        customer=customer,
        amount="150.00",
        due_date=due_date,
        status=Invoice.Status.PENDING,
    )

    scan_upcoming_invoices()

    event = OutboxEvent.objects.filter(event_type="payment.due_soon").first()
    assert event is not None
    assert event.payload["invoice_id"] == str(inv.id)
    assert event.payload["days_until_due"] == 3


@pytest.mark.django_db
def test_scan_upcoming_invoices_skips_non_pending(customer):
    import datetime

    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_upcoming_invoices
    from shared.models import OutboxEvent

    due_date = datetime.date.today() + datetime.timedelta(days=3)
    Invoice.objects.create(
        customer=customer,
        amount="150.00",
        due_date=due_date,
        status=Invoice.Status.PAID,
    )

    scan_upcoming_invoices()

    assert not OutboxEvent.objects.filter(event_type="payment.due_soon").exists()


@pytest.mark.django_db
def test_scan_upcoming_invoices_skips_wrong_date(customer):
    import datetime

    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_upcoming_invoices
    from shared.models import OutboxEvent

    # Due tomorrow — not in 3 days
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    Invoice.objects.create(
        customer=customer,
        amount="150.00",
        due_date=tomorrow,
        status=Invoice.Status.PENDING,
    )

    scan_upcoming_invoices()

    assert not OutboxEvent.objects.filter(event_type="payment.due_soon").exists()


@pytest.mark.django_db
def test_scan_upcoming_invoices_logs_error_and_continues(customer):
    import datetime

    from apps.billing.models import Invoice
    from apps.billing.tasks import scan_upcoming_invoices
    from shared.models import OutboxEvent

    due_date = datetime.date.today() + datetime.timedelta(days=3)
    Invoice.objects.create(
        customer=customer, amount="100.00", due_date=due_date, status=Invoice.Status.PENDING
    )
    Invoice.objects.create(
        customer=customer, amount="200.00", due_date=due_date, status=Invoice.Status.PENDING
    )

    create_calls = []
    original_create = OutboxEvent.objects.create

    def patched_create(**kwargs):
        create_calls.append(kwargs)
        if len(create_calls) == 1:
            raise Exception("transient error")
        return original_create(**kwargs)

    with patch.object(OutboxEvent.objects, "create", side_effect=patched_create):
        scan_upcoming_invoices()

    # Second invoice's event was still created despite first failure
    assert OutboxEvent.objects.filter(event_type="payment.due_soon").count() == 1
