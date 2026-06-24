"""Unit tests for apps/notifications/handlers.py.

Each handler is called directly with a synthetic payload and mocked
Celery task .delay() calls so no broker is needed.
"""

from unittest.mock import patch
import uuid

import pytest


def _id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# email_payment_confirmed
# ---------------------------------------------------------------------------


@patch("apps.notifications.tasks.send_payment_confirmed_email")
def test_email_payment_confirmed_dispatches_task(mock_task):
    from apps.notifications.handlers import email_payment_confirmed

    event_id = _id()
    invoice_id = _id()
    email_payment_confirmed({"invoice_id": invoice_id}, event_id)
    mock_task.delay.assert_called_once_with(invoice_id, event_id)


# ---------------------------------------------------------------------------
# renew_subscription_on_payment
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_renew_subscription_on_payment_no_subscription_id_is_noop():
    from apps.notifications.handlers import renew_subscription_on_payment

    # payload without subscription_id should return early without error
    renew_subscription_on_payment({"invoice_id": _id()}, _id())


@pytest.mark.django_db
def test_renew_subscription_on_payment_missing_subscription_returns_early():
    from apps.notifications.handlers import renew_subscription_on_payment

    renew_subscription_on_payment(
        {"invoice_id": _id(), "subscription_id": str(uuid.uuid4())}, _id()
    )


@pytest.mark.django_db
def test_renew_subscription_on_payment_active_subscription_calls_renew(customer):
    from django.utils import timezone

    from apps.notifications.handlers import renew_subscription_on_payment
    from apps.products.models import Pricing, Product
    from apps.subscriptions.models import Subscription

    product = Product.objects.create(name="P", slug=f"p-{uuid.uuid4().hex[:8]}")
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now(),
    )

    with patch("apps.subscriptions.commands.RenewSubscriptionCommand.execute") as mock_exec:
        renew_subscription_on_payment({"invoice_id": _id(), "subscription_id": str(sub.id)}, _id())
        mock_exec.assert_called_once_with(str(sub.id))


@pytest.mark.django_db
def test_renew_subscription_on_payment_logs_error_on_exception(customer):
    from django.utils import timezone

    from apps.notifications.handlers import renew_subscription_on_payment
    from apps.products.models import Pricing, Product
    from apps.subscriptions.models import Subscription

    product = Product.objects.create(name="P2", slug=f"p2-{uuid.uuid4().hex[:8]}")
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now(),
    )

    with patch(
        "apps.subscriptions.commands.RenewSubscriptionCommand.execute",
        side_effect=Exception("boom"),
    ):
        # Should not raise — error is logged only
        renew_subscription_on_payment({"invoice_id": _id(), "subscription_id": str(sub.id)}, _id())


# ---------------------------------------------------------------------------
# email_payment_overdue
# ---------------------------------------------------------------------------


@patch("apps.notifications.tasks.send_payment_overdue_email")
def test_email_payment_overdue_dispatches_task(mock_task):
    from apps.notifications.handlers import email_payment_overdue

    event_id = _id()
    invoice_id = _id()
    email_payment_overdue({"invoice_id": invoice_id}, event_id)
    mock_task.delay.assert_called_once_with(invoice_id, event_id)


# ---------------------------------------------------------------------------
# email_customer_cancelled
# ---------------------------------------------------------------------------


@patch("apps.notifications.tasks.send_customer_cancelled_email")
def test_email_customer_cancelled_dispatches_task(mock_task):
    from apps.notifications.handlers import email_customer_cancelled

    event_id = _id()
    customer_id = _id()
    email_customer_cancelled({"customer_id": customer_id}, event_id)
    mock_task.delay.assert_called_once_with(customer_id, event_id)


# ---------------------------------------------------------------------------
# log_charge_registered
# ---------------------------------------------------------------------------


def test_log_charge_registered_does_not_raise():
    from apps.notifications.handlers import log_charge_registered

    log_charge_registered({"invoice_id": _id(), "asaas_id": "pay_abc123"}, _id())


@patch("apps.notifications.tasks.send_invoice_ready_email")
def test_email_invoice_ready_dispatches_task(mock_task):
    from apps.notifications.handlers import email_invoice_ready

    event_id = _id()
    invoice_id = _id()
    email_invoice_ready({"invoice_id": invoice_id, "asaas_id": "pay_xyz"}, event_id)
    mock_task.delay.assert_called_once_with(invoice_id, event_id)


# ---------------------------------------------------------------------------
# provision_asaas_customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_provision_asaas_customer_calls_command(customer):
    from apps.notifications.handlers import provision_asaas_customer

    with patch("apps.billing.customer_commands.ProvisionAsaasCustomerCommand.execute") as mock_exec:
        provision_asaas_customer({"customer_id": str(customer.id)}, _id())
        mock_exec.assert_called_once_with(str(customer.id))


@pytest.mark.django_db
def test_provision_asaas_customer_reraises_on_exception(customer):
    from apps.notifications.handlers import provision_asaas_customer

    with patch(
        "apps.billing.customer_commands.ProvisionAsaasCustomerCommand.execute",
        side_effect=RuntimeError("asaas down"),
    ):
        with pytest.raises(RuntimeError, match="asaas down"):
            provision_asaas_customer({"customer_id": str(customer.id)}, _id())


# ---------------------------------------------------------------------------
# register_renewal_charge
# ---------------------------------------------------------------------------


def test_register_renewal_charge_calls_command():
    from apps.notifications.handlers import register_renewal_charge

    invoice_id = _id()
    with patch("apps.billing.commands.RegisterChargeCommand.execute") as mock_exec:
        register_renewal_charge({"invoice_id": invoice_id}, _id())
        mock_exec.assert_called_once()


def test_register_renewal_charge_swallows_exception():
    from apps.notifications.handlers import register_renewal_charge

    with patch(
        "apps.billing.commands.RegisterChargeCommand.execute",
        side_effect=Exception("gateway error"),
    ):
        # must not propagate
        register_renewal_charge({"invoice_id": _id()}, _id())


# ---------------------------------------------------------------------------
# email_invitation
# ---------------------------------------------------------------------------


@patch("apps.notifications.tasks.send_invitation_email")
def test_email_invitation_dispatches_task(mock_task):
    from apps.notifications.handlers import email_invitation

    event_id = _id()
    invitation_id = _id()
    email_invitation({"invitation_id": invitation_id}, event_id)
    mock_task.delay.assert_called_once_with(invitation_id, event_id)


# ---------------------------------------------------------------------------
# log_invitation_accepted
# ---------------------------------------------------------------------------


def test_log_invitation_accepted_does_not_raise():
    from apps.notifications.handlers import log_invitation_accepted

    log_invitation_accepted(
        {"invitation_id": _id(), "customer_id": _id(), "user_id": _id()},
        _id(),
    )


# ---------------------------------------------------------------------------
# Subscription email handlers
# ---------------------------------------------------------------------------


@patch("apps.notifications.tasks.send_subscription_suspended_email")
def test_email_subscription_suspended(mock_task):
    from apps.notifications.handlers import email_subscription_suspended

    sub_id = _id()
    event_id = _id()
    email_subscription_suspended({"subscription_id": sub_id}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id)


@patch("apps.notifications.tasks.send_subscription_expired_email")
def test_email_subscription_expired(mock_task):
    from apps.notifications.handlers import email_subscription_expired

    sub_id = _id()
    event_id = _id()
    email_subscription_expired({"subscription_id": sub_id}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id)


@patch("apps.notifications.tasks.send_subscription_grace_period_email")
def test_email_grace_period(mock_task):
    from apps.notifications.handlers import email_grace_period

    sub_id = _id()
    event_id = _id()
    email_grace_period({"subscription_id": sub_id}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id)


@patch("apps.notifications.tasks.send_subscription_renewed_email")
def test_email_subscription_renewed(mock_task):
    from apps.notifications.handlers import email_subscription_renewed

    sub_id = _id()
    event_id = _id()
    email_subscription_renewed({"subscription_id": sub_id}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id)


@patch("apps.notifications.tasks.send_subscription_cancelled_email")
def test_email_subscription_cancelled(mock_task):
    from apps.notifications.handlers import email_subscription_cancelled

    sub_id = _id()
    event_id = _id()
    email_subscription_cancelled({"subscription_id": sub_id}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id)


@patch("apps.notifications.tasks.send_plan_changed_email")
def test_email_plan_changed(mock_task):
    from apps.notifications.handlers import email_plan_changed

    sub_id = _id()
    event_id = _id()
    email_plan_changed({"subscription_id": sub_id}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id)


@patch("apps.notifications.tasks.send_subscription_expiring_soon_email")
def test_email_expiring_soon_with_days(mock_task):
    from apps.notifications.handlers import email_expiring_soon

    sub_id = _id()
    event_id = _id()
    email_expiring_soon({"subscription_id": sub_id, "days_remaining": 7}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id, 7)


@patch("apps.notifications.tasks.send_subscription_expiring_soon_email")
def test_email_expiring_soon_default_days(mock_task):
    from apps.notifications.handlers import email_expiring_soon

    sub_id = _id()
    event_id = _id()
    email_expiring_soon({"subscription_id": sub_id}, event_id)
    mock_task.delay.assert_called_once_with(sub_id, event_id, 3)


@patch("apps.notifications.tasks.send_quota_warning_email")
def test_email_quota_warning(mock_task):
    from apps.notifications.handlers import email_quota_warning

    customer_id = _id()
    event_id = _id()
    email_quota_warning({"customer_id": customer_id, "usage_pct": 85.0, "threshold": 80}, event_id)
    mock_task.delay.assert_called_once_with(customer_id, event_id, 85.0, 80)


# ---------------------------------------------------------------------------
# In-app notification handlers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_in_app_payment_confirmed_creates_notification(customer, invoice):
    from apps.notifications.handlers import in_app_payment_confirmed
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_payment_confirmed({"invoice_id": str(invoice.id)}, event_id)

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "payment.processed"
    assert "paga" in notif.body


@pytest.mark.django_db
def test_in_app_payment_confirmed_missing_invoice_is_noop():
    from apps.notifications.handlers import in_app_payment_confirmed
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_payment_confirmed({"invoice_id": str(uuid.uuid4())}, event_id)
    assert not Notification.objects.filter(outbox_event_id=event_id).exists()


@pytest.mark.django_db
def test_in_app_payment_overdue_creates_notification(customer, invoice):
    from apps.notifications.handlers import in_app_payment_overdue
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_payment_overdue({"invoice_id": str(invoice.id)}, event_id)

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "payment.failed"
    assert "vencida" in notif.body


@pytest.mark.django_db
def test_in_app_payment_overdue_missing_invoice_is_noop():
    from apps.notifications.handlers import in_app_payment_overdue
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_payment_overdue({"invoice_id": str(uuid.uuid4())}, event_id)
    assert not Notification.objects.filter(outbox_event_id=event_id).exists()


@pytest.mark.django_db
def test_in_app_expiring_soon_creates_notification(customer):
    from apps.notifications.handlers import in_app_expiring_soon
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_expiring_soon({"customer_id": str(customer.id), "days_remaining": 2}, event_id)

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert "2 dias" in notif.subject or "2 dia" in notif.subject


@pytest.mark.django_db
def test_in_app_expiring_soon_singular_day(customer):
    from apps.notifications.handlers import in_app_expiring_soon
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_expiring_soon({"customer_id": str(customer.id), "days_remaining": 1}, event_id)
    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert "1 dia" in notif.subject


@pytest.mark.django_db
def test_in_app_subscription_renewed(customer):
    from apps.notifications.handlers import in_app_subscription_renewed
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_subscription_renewed({"customer_id": str(customer.id)}, event_id)
    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "subscription.renewed"


@pytest.mark.django_db
def test_in_app_subscription_suspended(customer):
    from apps.notifications.handlers import in_app_subscription_suspended
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_subscription_suspended({"customer_id": str(customer.id)}, event_id)
    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "subscription.suspended"


@pytest.mark.django_db
def test_in_app_subscription_expired(customer):
    from apps.notifications.handlers import in_app_subscription_expired
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_subscription_expired({"customer_id": str(customer.id)}, event_id)
    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "subscription.expired"


@pytest.mark.django_db
def test_in_app_grace_period(customer):
    from apps.notifications.handlers import in_app_grace_period
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_grace_period({"customer_id": str(customer.id)}, event_id)
    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "subscription.grace_period"


@pytest.mark.django_db
def test_in_app_plan_changed(customer):
    from apps.notifications.handlers import in_app_plan_changed
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_plan_changed({"customer_id": str(customer.id)}, event_id)
    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "subscription.plan_changed"


@pytest.mark.django_db
def test_email_payment_due_soon_dispatches_task(invoice):
    from unittest.mock import patch

    from apps.notifications.handlers import email_payment_due_soon

    event_id = _id()
    with patch("apps.notifications.tasks.send_payment_due_soon_email.delay") as mock_delay:
        email_payment_due_soon({"invoice_id": str(invoice.id)}, event_id)
        mock_delay.assert_called_once_with(str(invoice.id), event_id)


@pytest.mark.django_db
def test_in_app_payment_due_soon(customer):
    from apps.notifications.handlers import in_app_payment_due_soon
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_payment_due_soon(
        {"customer_id": str(customer.id), "amount": "99.00", "days_until_due": 3},
        event_id,
    )
    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "payment.due_soon"
    assert "3 dias" in notif.subject


@pytest.mark.django_db
def test_in_app_idempotent_on_retry(customer, invoice):
    """get_or_create prevents duplicate notifications when handler runs twice (outbox retry)."""
    from apps.notifications.handlers import in_app_payment_confirmed
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_payment_confirmed({"invoice_id": str(invoice.id)}, event_id)
    in_app_payment_confirmed({"invoice_id": str(invoice.id)}, event_id)
    assert Notification.objects.filter(outbox_event_id=event_id).count() == 1


# ---------------------------------------------------------------------------
# customer.suspended handlers
# ---------------------------------------------------------------------------


@patch("apps.notifications.tasks.send_customer_suspended_email")
def test_email_customer_suspended_dispatches_task(mock_task):
    from apps.notifications.handlers import email_customer_suspended

    customer_id = _id()
    event_id = _id()
    email_customer_suspended({"customer_id": customer_id}, event_id)
    mock_task.delay.assert_called_once_with(customer_id, event_id)


@pytest.mark.django_db
def test_in_app_customer_suspended_creates_notification(customer):
    from apps.notifications.handlers import in_app_customer_suspended
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_customer_suspended({"customer_id": str(customer.id)}, event_id)

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "customer.suspended"
    assert "suspensa" in notif.body


# ---------------------------------------------------------------------------
# customer.reactivated handlers
# ---------------------------------------------------------------------------


@patch("apps.notifications.tasks.send_customer_reactivated_email")
def test_email_customer_reactivated_dispatches_task(mock_task):
    from apps.notifications.handlers import email_customer_reactivated

    customer_id = _id()
    event_id = _id()
    email_customer_reactivated({"customer_id": customer_id}, event_id)
    mock_task.delay.assert_called_once_with(customer_id, event_id)


@pytest.mark.django_db
def test_in_app_customer_reactivated_creates_notification(customer):
    from apps.notifications.handlers import in_app_customer_reactivated
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_customer_reactivated({"customer_id": str(customer.id)}, event_id)

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "customer.reactivated"
    assert "reativada" in notif.body


# ---------------------------------------------------------------------------
# in_app_service_provisioned
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_in_app_service_provisioned_creates_notification(customer):
    from apps.notifications.handlers import in_app_service_provisioned
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_service_provisioned({"customer_id": str(customer.id), "service_key": "n8n"}, event_id)

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert notif.event_type == "service.provisioned"
    assert "n8n" in notif.subject
    assert "dashboard" in notif.body


@pytest.mark.django_db
def test_in_app_service_provisioned_uses_label_map(customer):
    from apps.notifications.handlers import in_app_service_provisioned
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_service_provisioned(
        {"customer_id": str(customer.id), "service_key": "keycloak"}, event_id
    )

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert "Keycloak" in notif.subject


@pytest.mark.django_db
def test_in_app_service_provisioned_falls_back_to_key(customer):
    """Unknown service_key falls back to the raw key string."""
    from apps.notifications.handlers import in_app_service_provisioned
    from apps.notifications.models import Notification

    event_id = _id()
    in_app_service_provisioned(
        {"customer_id": str(customer.id), "service_key": "unknown-future-svc"}, event_id
    )

    notif = Notification.objects.get(outbox_event_id=event_id, channel=Notification.Channel.IN_APP)
    assert "unknown-future-svc" in notif.subject


@pytest.mark.django_db
def test_in_app_service_provisioned_idempotent(customer):
    """Same event_id must not create duplicate Notification rows."""
    from apps.notifications.handlers import in_app_service_provisioned
    from apps.notifications.models import Notification

    event_id = _id()
    payload = {"customer_id": str(customer.id), "service_key": "proxmox"}
    in_app_service_provisioned(payload, event_id)
    in_app_service_provisioned(payload, event_id)  # second call must be a no-op

    assert Notification.objects.filter(outbox_event_id=event_id).count() == 1
