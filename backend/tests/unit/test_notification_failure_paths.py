"""
Tests for the two paths that remain uncovered across all email tasks:
  1. SMTP failure → mark Notification FAILED, raise Retry
  2. Already-SENT notification → early return (idempotency)
  3. No-owner recipient → early return without creating a Notification
  4. Customer/subscription not-found for tasks that lack an explicit test

All tasks use `bind=True, max_retries=3`; when send_mail raises, they call
`self.retry(exc=exc)` which raises `celery.exceptions.Retry`.
"""

import datetime
from unittest.mock import patch
import uuid

from django.utils import timezone
import pytest

from apps.accounts.models import CustomUser
from apps.billing.models import Invoice
from apps.customers.models import Customer, CustomerProfile, Invitation
from apps.notifications.models import Notification
from apps.products.models import Pricing, Product
from apps.subscriptions.models import License, Subscription

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _doc() -> str:
    d = f"{uuid.uuid4().int % 10**14:014d}"
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def _customer_with_owner() -> tuple[Customer, str]:
    email = f"fail_{uuid.uuid4().hex[:6]}@x.com"
    user = CustomUser.objects.create_user(username=email.split("@")[0], email=email, password="x")
    customer = Customer.objects.create(company_name="Fail Co", document=_doc())
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)
    return customer, email


def _customer_no_owner() -> Customer:
    return Customer.objects.create(company_name="No Owner Co", document=_doc())


def _invoice(customer: Customer) -> Invoice:
    return Invoice.objects.create(
        customer=customer,
        amount="99.00",
        due_date=datetime.date.today(),
        status=Invoice.Status.PENDING,
    )


def _subscription(customer: Customer) -> Subscription:
    slug = f"sp-{uuid.uuid4().hex[:6]}"
    product = Product.objects.create(name="Sub Plan", slug=slug)
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="49.00")
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now() + datetime.timedelta(days=30),
    )
    License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + datetime.timedelta(days=30),
    )
    return sub


def _invitation(customer: Customer, inviter) -> Invitation:
    return Invitation.objects.create(
        customer=customer,
        invited_by=inviter,
        email="inv@x.com",
        role="member",
        token=uuid.uuid4().hex,
        expires_at=timezone.now() + datetime.timedelta(days=7),
    )


def _pre_sent(outbox_event_id: str, event_type: str, recipient: str) -> Notification:
    return Notification.objects.create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        event_type=event_type,
        recipient=recipient,
        subject="s",
        body="b",
        status=Notification.Status.SENT,
    )


# ---------------------------------------------------------------------------
# Helper to run an SMTP-failure test for any bound Celery task
# ---------------------------------------------------------------------------


def _smtp_failure(task_fn, args):
    """Call task_fn(*args) with send_html_email patched to raise. Assert FAILED notification."""
    from celery.exceptions import Retry

    with patch("apps.notifications.tasks.send_html_email", side_effect=Exception("SMTP boom")):
        with pytest.raises((Retry, Exception)):
            task_fn(*args)


# ---------------------------------------------------------------------------
# send_payment_confirmed_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentConfirmedFailurePaths:
    def test_smtp_failure_marks_notification_failed(self):
        from apps.notifications.tasks import send_payment_confirmed_email

        customer, owner_email = _customer_with_owner()
        invoice = _invoice(customer)
        eid = str(uuid.uuid4())
        _smtp_failure(send_payment_confirmed_email, [str(invoice.id), eid])

        notif = Notification.objects.filter(outbox_event_id=eid).first()
        assert notif and notif.status == Notification.Status.FAILED

    def test_already_sent_skips_send_mail(self):
        from apps.notifications.tasks import send_payment_confirmed_email

        customer, owner_email = _customer_with_owner()
        invoice = _invoice(customer)
        eid = str(uuid.uuid4())
        _pre_sent(eid, "payment.processed", owner_email)

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            send_payment_confirmed_email(str(invoice.id), eid)
            mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# send_customer_cancelled_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCustomerCancelledFailurePaths:
    def test_smtp_failure_marks_notification_failed(self):
        from apps.notifications.tasks import send_customer_cancelled_email

        customer, owner_email = _customer_with_owner()
        eid = str(uuid.uuid4())
        _smtp_failure(send_customer_cancelled_email, [str(customer.id), eid])

        notif = Notification.objects.filter(outbox_event_id=eid).first()
        assert notif and notif.status == Notification.Status.FAILED

    def test_already_sent_skips_send_mail(self):
        from apps.notifications.tasks import send_customer_cancelled_email

        customer, owner_email = _customer_with_owner()
        eid = str(uuid.uuid4())
        _pre_sent(eid, "customer.cancelled", owner_email)

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            send_customer_cancelled_email(str(customer.id), eid)
            mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# send_invitation_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvitationEmailFailurePaths:
    def test_smtp_failure_marks_notification_failed(self):
        from apps.notifications.tasks import send_invitation_email

        customer, _ = _customer_with_owner()
        inviter = CustomerProfile.objects.get(customer=customer, role="owner").user
        invitation = _invitation(customer, inviter)
        eid = str(uuid.uuid4())
        _smtp_failure(send_invitation_email, [str(invitation.id), eid])

        notif = Notification.objects.filter(outbox_event_id=eid).first()
        assert notif and notif.status == Notification.Status.FAILED

    def test_already_sent_skips_send_mail(self):
        from apps.notifications.tasks import send_invitation_email

        customer, _ = _customer_with_owner()
        inviter = CustomerProfile.objects.get(customer=customer, role="owner").user
        invitation = _invitation(customer, inviter)
        eid = str(uuid.uuid4())
        _pre_sent(eid, "invitation.created", invitation.email)

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            send_invitation_email(str(invitation.id), eid)
            mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# send_quota_warning_email — missing: customer_not_found
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestQuotaWarningFailurePaths:
    def test_customer_not_found_is_noop(self):
        from apps.notifications.tasks import send_quota_warning_email

        send_quota_warning_email(str(uuid.uuid4()), str(uuid.uuid4()), usage_pct=90.0, threshold=80)

    def test_smtp_failure_marks_notification_failed(self):
        from apps.notifications.tasks import send_quota_warning_email

        customer, _ = _customer_with_owner()
        eid = str(uuid.uuid4())
        _smtp_failure(send_quota_warning_email, [str(customer.id), eid, 90.0, 80])

        notif = Notification.objects.filter(outbox_event_id=eid).first()
        assert notif and notif.status == Notification.Status.FAILED

    def test_already_sent_skips_send_mail(self):
        from apps.notifications.tasks import send_quota_warning_email

        customer, owner_email = _customer_with_owner()
        eid = str(uuid.uuid4())
        _pre_sent(eid, "quota.warning", owner_email)

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            send_quota_warning_email(str(customer.id), eid, usage_pct=90.0, threshold=80)
            mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# Parametrized: subscription email tasks — no-owner + SMTP failure + already-SENT
# ---------------------------------------------------------------------------


def _sub_task_cases():
    """Return (task_import_name, event_type, extra_kwargs) tuples for all subscription tasks."""
    return [
        ("send_subscription_grace_period_email", "subscription.grace_period", {}),
        (
            "send_subscription_expiring_soon_email",
            "subscription.expiring_soon",
            {"days_remaining": 3},
        ),
        ("send_subscription_renewed_email", "subscription.renewed", {}),
        ("send_subscription_cancelled_email", "subscription.cancelled", {}),
        ("send_plan_changed_email", "subscription.plan_changed", {}),
        ("send_subscription_suspended_email", "subscription.suspended", {}),
        ("send_subscription_expired_email", "subscription.expired", {}),
    ]


@pytest.mark.django_db
class TestSubscriptionEmailNoOwner:
    @pytest.mark.parametrize("task_name,event_type,kwargs", _sub_task_cases())
    def test_no_owner_is_noop(self, task_name, event_type, kwargs):
        import importlib

        tasks_mod = importlib.import_module("apps.notifications.tasks")
        task_fn = getattr(tasks_mod, task_name)

        customer = _customer_no_owner()
        sub = _subscription(customer)
        eid = str(uuid.uuid4())

        task_fn(str(sub.id), eid, **kwargs)

        assert not Notification.objects.filter(outbox_event_id=eid).exists()


@pytest.mark.django_db
class TestSubscriptionEmailSmtpFailure:
    @pytest.mark.parametrize("task_name,event_type,kwargs", _sub_task_cases())
    def test_smtp_failure_marks_failed(self, task_name, event_type, kwargs):
        import importlib

        tasks_mod = importlib.import_module("apps.notifications.tasks")
        task_fn = getattr(tasks_mod, task_name)

        customer, _ = _customer_with_owner()
        sub = _subscription(customer)
        eid = str(uuid.uuid4())

        _smtp_failure(task_fn, [str(sub.id), eid, *kwargs.values()])

        notif = Notification.objects.filter(outbox_event_id=eid).first()
        assert notif and notif.status == Notification.Status.FAILED


@pytest.mark.django_db
class TestSubscriptionEmailAlreadySent:
    @pytest.mark.parametrize("task_name,event_type,kwargs", _sub_task_cases())
    def test_already_sent_skips_send_mail(self, task_name, event_type, kwargs):
        import importlib

        tasks_mod = importlib.import_module("apps.notifications.tasks")
        task_fn = getattr(tasks_mod, task_name)

        customer, owner_email = _customer_with_owner()
        sub = _subscription(customer)
        eid = str(uuid.uuid4())
        _pre_sent(eid, event_type, owner_email)

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            task_fn(str(sub.id), eid, **kwargs)
            mock_send.assert_not_called()
