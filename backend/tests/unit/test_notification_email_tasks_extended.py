"""Extended tests for apps/notifications/tasks.py — subscription and misc email tasks.

Pattern per task:
- success: sends email, Notification.SENT
- not_found: early return, no error
"""

import datetime
import uuid
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
import pytest

from apps.accounts.models import CustomUser
from apps.billing.models import Invoice
from apps.customers.models import Customer, CustomerProfile, Invitation
from apps.notifications.models import Notification
from apps.products.models import Pricing, Product
from apps.subscriptions.models import License, Subscription

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cid() -> str:
    return str(uuid.uuid4())


def _make_customer_with_owner() -> tuple[Customer, str]:
    email = f"owner_{uuid.uuid4().hex[:6]}@notifext.com"
    user = CustomUser.objects.create_user(username=email.split("@")[0], email=email, password="x")
    doc_digits = f"{uuid.uuid4().int % 10**14:014d}"
    doc = f"{doc_digits[:2]}.{doc_digits[2:5]}.{doc_digits[5:8]}/{doc_digits[8:12]}-{doc_digits[12:14]}"
    customer = Customer.objects.create(company_name="Notif Extended Co", document=doc)
    CustomerProfile.objects.create(user=user, customer=customer, role=CustomerProfile.Role.OWNER)
    return customer, email


def _make_subscription(customer: Customer) -> Subscription:
    slug = f"plan-{uuid.uuid4().hex[:6]}"
    product = Product.objects.create(name="Notif Plan", slug=slug)
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
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


# ---------------------------------------------------------------------------
# send_customer_cancelled_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendCustomerCancelledEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_marks_sent(self):
        from apps.notifications.tasks import send_customer_cancelled_email

        customer, _ = _make_customer_with_owner()
        event_id = _cid()
        send_customer_cancelled_email(str(customer.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "customer.cancelled"

    def test_customer_not_found_is_noop(self):
        from apps.notifications.tasks import send_customer_cancelled_email

        send_customer_cancelled_email(_cid(), _cid())

    def test_no_owner_profile_is_noop(self):
        from apps.notifications.tasks import send_customer_cancelled_email

        doc_digits = f"{uuid.uuid4().int % 10**14:014d}"
        doc = f"{doc_digits[:2]}.{doc_digits[2:5]}.{doc_digits[5:8]}/{doc_digits[8:12]}-{doc_digits[12:14]}"
        customer = Customer.objects.create(company_name="No Owner", document=doc)
        event_id = _cid()
        send_customer_cancelled_email(str(customer.id), event_id)
        assert not Notification.objects.filter(outbox_event_id=event_id).exists()


# ---------------------------------------------------------------------------
# send_invitation_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendInvitationEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_invitation_email(self):
        from apps.notifications.tasks import send_invitation_email

        customer, owner_email = _make_customer_with_owner()
        inviter = CustomUser.objects.get(email=owner_email)
        invitation = Invitation.objects.create(
            customer=customer,
            invited_by=inviter,
            email="invitee@notifext.com",
            role="member",
            token=uuid.uuid4().hex,
            expires_at=timezone.now() + datetime.timedelta(days=7),
        )
        event_id = _cid()
        send_invitation_email(str(invitation.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "invitation.created"

    def test_invitation_not_found_is_noop(self):
        from apps.notifications.tasks import send_invitation_email

        send_invitation_email(_cid(), _cid())


# ---------------------------------------------------------------------------
# Subscription email tasks — one test each (success + not_found)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSubscriptionEmailTasks:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_grace_period_email(self):
        from apps.notifications.tasks import send_subscription_grace_period_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = _cid()
        send_subscription_grace_period_email(str(sub.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_grace_period_not_found(self):
        from apps.notifications.tasks import send_subscription_grace_period_email

        send_subscription_grace_period_email(_cid(), _cid())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_expiring_soon_email(self):
        from apps.notifications.tasks import send_subscription_expiring_soon_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = _cid()
        send_subscription_expiring_soon_email(str(sub.id), event_id, days_remaining=3)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_expiring_soon_not_found(self):
        from apps.notifications.tasks import send_subscription_expiring_soon_email

        send_subscription_expiring_soon_email(_cid(), _cid(), days_remaining=7)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_quota_warning_email(self):
        from apps.notifications.tasks import send_quota_warning_email

        customer, _ = _make_customer_with_owner()
        event_id = _cid()
        send_quota_warning_email(str(customer.id), event_id, usage_pct=85.0, threshold=80)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_quota_warning_no_owner_is_noop(self):
        from apps.notifications.tasks import send_quota_warning_email

        doc_digits = f"{uuid.uuid4().int % 10**14:014d}"
        doc = f"{doc_digits[:2]}.{doc_digits[2:5]}.{doc_digits[5:8]}/{doc_digits[8:12]}-{doc_digits[12:14]}"
        customer = Customer.objects.create(company_name="No Owner Quota", document=doc)
        event_id = _cid()
        send_quota_warning_email(str(customer.id), event_id, usage_pct=90.0, threshold=80)
        assert not Notification.objects.filter(outbox_event_id=event_id).exists()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_subscription_renewed_email(self):
        from apps.notifications.tasks import send_subscription_renewed_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = _cid()
        send_subscription_renewed_email(str(sub.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_subscription_renewed_not_found(self):
        from apps.notifications.tasks import send_subscription_renewed_email

        send_subscription_renewed_email(_cid(), _cid())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_subscription_cancelled_email(self):
        from apps.notifications.tasks import send_subscription_cancelled_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = _cid()
        send_subscription_cancelled_email(str(sub.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_subscription_cancelled_not_found(self):
        from apps.notifications.tasks import send_subscription_cancelled_email

        send_subscription_cancelled_email(_cid(), _cid())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_plan_changed_email(self):
        from apps.notifications.tasks import send_plan_changed_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = _cid()
        send_plan_changed_email(str(sub.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_plan_changed_not_found(self):
        from apps.notifications.tasks import send_plan_changed_email

        send_plan_changed_email(_cid(), _cid())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_subscription_suspended_email(self):
        from apps.notifications.tasks import send_subscription_suspended_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = _cid()
        send_subscription_suspended_email(str(sub.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_subscription_suspended_not_found(self):
        from apps.notifications.tasks import send_subscription_suspended_email

        send_subscription_suspended_email(_cid(), _cid())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_subscription_expired_email(self):
        from apps.notifications.tasks import send_subscription_expired_email

        customer, _ = _make_customer_with_owner()
        sub = _make_subscription(customer)
        event_id = _cid()
        send_subscription_expired_email(str(sub.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT

    def test_send_subscription_expired_not_found(self):
        from apps.notifications.tasks import send_subscription_expired_email

        send_subscription_expired_email(_cid(), _cid())


# ---------------------------------------------------------------------------
# send_customer_suspended_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendCustomerSuspendedEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_marks_sent(self):
        from apps.notifications.tasks import send_customer_suspended_email

        customer, _ = _make_customer_with_owner()
        event_id = _cid()
        send_customer_suspended_email(str(customer.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "customer.suspended"

    def test_customer_not_found_is_noop(self):
        from apps.notifications.tasks import send_customer_suspended_email

        send_customer_suspended_email(_cid(), _cid())

    @pytest.mark.django_db
    def test_no_owner_profile_is_noop(self):
        from apps.notifications.tasks import send_customer_suspended_email

        doc_digits = f"{uuid.uuid4().int % 10**14:014d}"
        doc = f"{doc_digits[:2]}.{doc_digits[2:5]}.{doc_digits[5:8]}/{doc_digits[8:12]}-{doc_digits[12:14]}"
        customer = Customer.objects.create(company_name="No Owner Suspended", document=doc)
        event_id = _cid()
        send_customer_suspended_email(str(customer.id), event_id)
        assert not Notification.objects.filter(outbox_event_id=event_id).exists()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_idempotent_on_retry(self):
        from apps.notifications.tasks import send_customer_suspended_email

        customer, _ = _make_customer_with_owner()
        event_id = _cid()
        send_customer_suspended_email(str(customer.id), event_id)
        send_customer_suspended_email(str(customer.id), event_id)
        assert Notification.objects.filter(outbox_event_id=event_id).count() == 1


# ---------------------------------------------------------------------------
# send_customer_reactivated_email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendCustomerReactivatedEmail:
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_sends_email_and_marks_sent(self):
        from apps.notifications.tasks import send_customer_reactivated_email

        customer, _ = _make_customer_with_owner()
        event_id = _cid()
        send_customer_reactivated_email(str(customer.id), event_id)

        notif = Notification.objects.get(
            outbox_event_id=event_id, channel=Notification.Channel.EMAIL
        )
        assert notif.status == Notification.Status.SENT
        assert notif.event_type == "customer.reactivated"

    def test_customer_not_found_is_noop(self):
        from apps.notifications.tasks import send_customer_reactivated_email

        send_customer_reactivated_email(_cid(), _cid())

    @pytest.mark.django_db
    def test_no_owner_profile_is_noop(self):
        from apps.notifications.tasks import send_customer_reactivated_email

        doc_digits = f"{uuid.uuid4().int % 10**14:014d}"
        doc = f"{doc_digits[:2]}.{doc_digits[2:5]}.{doc_digits[5:8]}/{doc_digits[8:12]}-{doc_digits[12:14]}"
        customer = Customer.objects.create(company_name="No Owner Reactivated", document=doc)
        event_id = _cid()
        send_customer_reactivated_email(str(customer.id), event_id)
        assert not Notification.objects.filter(outbox_event_id=event_id).exists()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_idempotent_on_retry(self):
        from apps.notifications.tasks import send_customer_reactivated_email

        customer, _ = _make_customer_with_owner()
        event_id = _cid()
        send_customer_reactivated_email(str(customer.id), event_id)
        send_customer_reactivated_email(str(customer.id), event_id)
        assert Notification.objects.filter(outbox_event_id=event_id).count() == 1


@pytest.mark.django_db
class TestSendInvoiceReadyEmail:
    def _make_invoice(self) -> Invoice:
        customer, _ = _make_customer_with_owner()
        return Invoice.objects.create(
            customer=customer,
            amount="149.00",
            due_date=timezone.now().date() + datetime.timedelta(days=5),
            status=Invoice.Status.PENDING,
            billing_type=Invoice.BillingType.BOLETO,
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_URL="https://app.papermoon.com.br",
    )
    def test_uses_sanitized_asaas_payment_link(self):
        from apps.notifications.tasks import send_invoice_ready_email

        invoice = self._make_invoice()
        invoice.payment_url = "https://www.asaas.com/c/pay-123"
        invoice.save(update_fields=["payment_url"])

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            send_invoice_ready_email(str(invoice.id), _cid())

        assert mock_send.call_args.kwargs["context"]["cta_link"] == "https://www.asaas.com/c/pay-123"

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_URL="https://app.papermoon.com.br",
    )
    def test_falls_back_to_frontend_when_payment_url_is_untrusted(self):
        from apps.notifications.tasks import send_invoice_ready_email

        invoice = self._make_invoice()
        invoice.payment_url = "https://evil.example.com/pay-123"
        invoice.save(update_fields=["payment_url"])

        with patch("apps.notifications.tasks.send_html_email") as mock_send:
            send_invoice_ready_email(str(invoice.id), _cid())

        assert (
            mock_send.call_args.kwargs["context"]["cta_link"]
            == "https://app.papermoon.com.br/dashboard/invoices"
        )
