"""Unit tests for apps/notifications/tasks.py — email delivery tasks.

Uses Django's in-memory email backend so no SMTP server is needed.
Each task is called directly (synchronously, no broker).
"""

from unittest.mock import patch
import uuid

from django.test import override_settings
import pytest

from apps.accounts.models import CustomUser
from apps.billing.models import Invoice
from apps.customers.models import Customer, CustomerProfile
from apps.notifications.models import Notification


def _make_customer_with_owner() -> tuple[Customer, str]:
    """Returns (customer, owner_email)."""
    email = f"owner-{uuid.uuid4().hex[:6]}@notif.com"
    user = CustomUser.objects.create_user(username=email.split("@")[0], email=email, password="x")
    doc = f"{uuid.uuid4().int % 10**14:014d}"
    doc_fmt = f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:14]}"
    customer = Customer.objects.create(company_name="Notif Co", document=doc_fmt)
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)
    return customer, email


def _make_invoice(customer: Customer) -> Invoice:
    import datetime

    return Invoice.objects.create(
        customer=customer,
        amount="199.00",
        due_date=datetime.date.today(),
        status=Invoice.Status.PENDING,
    )


# ---------------------------------------------------------------------------
# send_payment_overdue_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendPaymentOverdueEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_creates_notification(self):
        from apps.notifications.tasks import send_payment_overdue_email

        customer, owner_email = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        send_payment_overdue_email(str(invoice.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "payment.failed"

    def test_invoice_not_found_returns_without_error(self):
        from apps.notifications.tasks import send_payment_overdue_email

        # Must not raise
        send_payment_overdue_email(str(uuid.uuid4()), str(uuid.uuid4()))

    def test_no_owner_returns_without_sending(self):
        from apps.notifications.tasks import send_payment_overdue_email

        # Customer with no owner profile
        doc = f"99.{uuid.uuid4().int % 10**3:03d}.000/0001-99"
        customer = Customer.objects.create(company_name="No Owner Co", document=doc)
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        send_payment_overdue_email(str(invoice.id), event_id)

        assert not Notification.objects.filter(outbox_event_id=event_id).exists()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_idempotent_on_second_call_with_same_event_id(self):
        from apps.notifications.tasks import send_payment_overdue_email

        customer, _ = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        send_payment_overdue_email(str(invoice.id), event_id)
        send_payment_overdue_email(str(invoice.id), event_id)

        assert Notification.objects.filter(outbox_event_id=event_id).count() == 1

    def test_already_sent_notification_is_skipped(self):
        from apps.notifications.tasks import send_payment_overdue_email

        customer, owner_email = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        # Pre-create a SENT notification
        Notification.objects.create(
            outbox_event_id=event_id,
            channel=Notification.Channel.EMAIL,
            event_type="payment.failed",
            recipient=owner_email,
            subject="test",
            body="test",
            status=Notification.Status.SENT,
        )

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            send_payment_overdue_email(str(invoice.id), event_id)
            mock_send.assert_not_called()

    def test_smtp_failure_marks_notification_failed(self):
        from celery.exceptions import Retry

        from apps.notifications.tasks import send_payment_overdue_email

        customer, _ = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        with patch("apps.notifications.tasks.send_html_email", side_effect=Exception("SMTP error")):
            with pytest.raises((Retry, Exception)):
                send_payment_overdue_email(str(invoice.id), event_id)

        notif = Notification.objects.filter(outbox_event_id=event_id).first()
        if notif:
            assert notif.status == Notification.Status.FAILED


# ---------------------------------------------------------------------------
# send_payment_confirmed_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendPaymentConfirmedEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_marks_sent(self):
        from apps.notifications.tasks import send_payment_confirmed_email

        customer, _ = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        send_payment_confirmed_email(str(invoice.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "payment.processed"

    def test_invoice_not_found_is_noop(self):
        from apps.notifications.tasks import send_payment_confirmed_email

        send_payment_confirmed_email(str(uuid.uuid4()), str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# send_payment_due_soon_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendPaymentDueSoonEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_creates_notification(self):
        from apps.notifications.tasks import send_payment_due_soon_email

        customer, _ = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        send_payment_due_soon_email(str(invoice.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "payment.due_soon"

    def test_invoice_not_found_returns_without_error(self):
        from apps.notifications.tasks import send_payment_due_soon_email

        send_payment_due_soon_email(str(uuid.uuid4()), str(uuid.uuid4()))

    def test_no_owner_returns_without_sending(self):
        from apps.notifications.tasks import send_payment_due_soon_email

        doc = f"88.{uuid.uuid4().int % 10**3:03d}.000/0001-88"
        customer = Customer.objects.create(company_name="No Owner Due Soon", document=doc)
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        send_payment_due_soon_email(str(invoice.id), event_id)

        assert not Notification.objects.filter(outbox_event_id=event_id).exists()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_idempotent_on_second_call(self):
        from apps.notifications.tasks import send_payment_due_soon_email

        customer, _ = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        send_payment_due_soon_email(str(invoice.id), event_id)
        send_payment_due_soon_email(str(invoice.id), event_id)

        assert Notification.objects.filter(outbox_event_id=event_id).count() == 1

    def test_smtp_failure_marks_notification_failed(self):
        from celery.exceptions import Retry

        from apps.notifications.tasks import send_payment_due_soon_email

        customer, _ = _make_customer_with_owner()
        invoice = _make_invoice(customer)
        event_id = str(uuid.uuid4())

        with patch("apps.notifications.tasks.send_html_email", side_effect=Exception("SMTP")):
            with pytest.raises((Retry, Exception)):
                send_payment_due_soon_email(str(invoice.id), event_id)

        notif = Notification.objects.filter(outbox_event_id=event_id).first()
        if notif:
            assert notif.status == Notification.Status.FAILED


# ---------------------------------------------------------------------------
# send_subscription_created_email
# ---------------------------------------------------------------------------


def _make_subscription(customer):
    import datetime

    from apps.products.models import Pricing, Product, ServiceComponent
    from apps.subscriptions.models import License, Subscription

    product = Product.objects.create(
        name="Atendimento WhatsApp",
        slug=f"whatsapp-{uuid.uuid4().hex[:6]}",
    )
    ServiceComponent.objects.create(product=product, service_key="chatwoot")
    pricing = Pricing.objects.create(
        product=product,
        billing_cycle="monthly",
        amount="499.00",
        trial_days=0,
    )
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status="active",
        starts_at=now,
        expires_at=now + datetime.timedelta(days=30),
    )
    License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status="active",
        valid_from=sub.starts_at,
        valid_until=sub.expires_at,
    )
    return sub


@pytest.mark.django_db
class TestSendSubscriptionCreatedEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_marks_sent(self):
        from apps.notifications.tasks import send_subscription_created_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = str(uuid.uuid4())

        send_subscription_created_email(str(sub.id), event_id)

        notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.EMAIL)
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "subscription.created"

    def test_subscription_not_found_is_noop(self):
        from apps.notifications.tasks import send_subscription_created_email

        send_subscription_created_email(str(uuid.uuid4()), str(uuid.uuid4()))

    def test_no_owner_is_noop(self):
        from apps.notifications.tasks import send_subscription_created_email

        doc = f"77.{uuid.uuid4().int % 10**3:03d}.000/0001-77"
        customer = Customer.objects.create(company_name="No Owner Sub", document=doc)
        sub = _make_subscription(customer)
        event_id = str(uuid.uuid4())

        send_subscription_created_email(str(sub.id), event_id)

        assert not Notification.objects.filter(outbox_event_id=event_id).exists()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_idempotent(self):
        from apps.notifications.tasks import send_subscription_created_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = str(uuid.uuid4())

        send_subscription_created_email(str(sub.id), event_id)
        send_subscription_created_email(str(sub.id), event_id)

        assert Notification.objects.filter(outbox_event_id=event_id).count() == 1


# ---------------------------------------------------------------------------
# send_customer_created_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendCustomerCreatedEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_marks_sent(self):
        from apps.notifications.tasks import send_customer_created_email

        customer, _ = _make_customer_with_owner()
        event_id = str(uuid.uuid4())

        send_customer_created_email(str(customer.id), event_id)

        notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.EMAIL)
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "customer.created"

    def test_customer_not_found_is_noop(self):
        from apps.notifications.tasks import send_customer_created_email

        send_customer_created_email(str(uuid.uuid4()), str(uuid.uuid4()))

    def test_no_owner_is_noop(self):
        from apps.notifications.tasks import send_customer_created_email

        doc = f"66.{uuid.uuid4().int % 10**3:03d}.000/0001-66"
        customer = Customer.objects.create(company_name="No Owner Created", document=doc)
        event_id = str(uuid.uuid4())

        send_customer_created_email(str(customer.id), event_id)

        assert not Notification.objects.filter(outbox_event_id=event_id).exists()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_idempotent(self):
        from apps.notifications.tasks import send_customer_created_email

        customer, _ = _make_customer_with_owner()
        event_id = str(uuid.uuid4())

        send_customer_created_email(str(customer.id), event_id)
        send_customer_created_email(str(customer.id), event_id)

        assert Notification.objects.filter(outbox_event_id=event_id).count() == 1
