"""
Unit tests for apps/provisioning/handlers.py.
All handlers are called directly (not via the outbox task queue).
Provisioners are mocked to avoid HTTP calls.
"""

import datetime
from unittest.mock import MagicMock, patch
import uuid

from django.utils import timezone
import pytest

from apps.customers.models import Customer
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.models import License, ServiceAccess, Subscription

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_customer() -> Customer:
    doc = f"{uuid.uuid4().int % 10**14:014d}"
    doc_fmt = f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:14]}"
    return Customer.objects.create(company_name="Prov Test Co", document=doc_fmt)


def _make_subscription_with_sa(customer: Customer, service_key: str = "n8n"):
    slug = f"prod-{uuid.uuid4().hex[:6]}"
    product = Product.objects.create(name="Prov Product", slug=slug)
    ServiceComponent.objects.create(product=product, service_key=service_key)
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now() + datetime.timedelta(days=30),
    )
    lic = License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + datetime.timedelta(days=30),
    )
    sa = ServiceAccess.objects.create(
        license=lic,
        service_key=service_key,
        status=ServiceAccess.Status.PROVISIONING,
    )
    return sub, lic, sa


def _make_mock_provisioner(service_key: str = "n8n") -> MagicMock:
    p = MagicMock()
    p.service_key = service_key
    p.provision.return_value = f"ext-{uuid.uuid4().hex[:8]}"
    return p


# ---------------------------------------------------------------------------
# provision_services (subscription.created)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProvisionServices:
    def test_provisions_service_and_marks_active(self):
        from apps.provisioning.handlers import provision_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        mock_prov = _make_mock_provisioner("n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            provision_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )

        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.ACTIVE
        assert sa.external_id == mock_prov.provision.return_value

    def test_marks_failed_when_provisioner_raises(self):
        from apps.provisioning.handlers import provision_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        mock_prov = _make_mock_provisioner("n8n")
        mock_prov.provision.side_effect = RuntimeError("API down")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            provision_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )

        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.FAILED
        assert "API down" in sa.error

    def test_skips_unknown_service_key(self):
        from apps.provisioning.handlers import provision_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=None):
            provision_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["unknown_svc"],
                },
                str(uuid.uuid4()),
            )

        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.PROVISIONING  # unchanged

    def test_skips_missing_service_access(self):
        from apps.provisioning.handlers import provision_services

        customer = _make_customer()
        mock_prov = _make_mock_provisioner("n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            # Should not raise — just log and continue
            provision_services(
                {
                    "license_id": str(uuid.uuid4()),  # nonexistent
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )


# ---------------------------------------------------------------------------
# _act_on_services (via suspend_services / deprovision_services)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestActOnServices:
    def test_suspend_services_calls_provisioner_suspend(self):
        from apps.provisioning.handlers import suspend_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        sa.status = ServiceAccess.Status.ACTIVE
        sa.external_id = "ext-abc"
        sa.save()
        mock_prov = _make_mock_provisioner("n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            suspend_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )

        mock_prov.suspend.assert_called_once_with(
            external_id="ext-abc", customer_id=str(customer.id)
        )

    def test_deprovision_services_calls_provisioner_deprovision(self):
        from apps.provisioning.handlers import deprovision_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        sa.external_id = "ext-xyz"
        sa.save()
        mock_prov = _make_mock_provisioner("n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            deprovision_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )

        mock_prov.deprovision.assert_called_once()

    def test_act_on_services_early_return_when_no_license_id(self):
        from apps.provisioning.handlers import suspend_services

        mock_prov = _make_mock_provisioner("n8n")
        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            suspend_services(
                {"customer_id": "cust-1", "service_keys": ["n8n"]},
                str(uuid.uuid4()),
            )
        mock_prov.suspend.assert_not_called()

    def test_act_on_services_logs_error_and_continues_on_exception(self):
        from apps.provisioning.handlers import suspend_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        mock_prov = _make_mock_provisioner("n8n")
        mock_prov.suspend.side_effect = RuntimeError("connection refused")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            # Should not raise
            suspend_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )

        mock_prov.suspend.assert_called_once()


# ---------------------------------------------------------------------------
# reactivate_services (subscription.renewed)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestReactivateServices:
    def test_reactivates_suspended_service_accesses(self):
        from apps.provisioning.handlers import reactivate_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        sa.status = ServiceAccess.Status.SUSPENDED
        sa.external_id = "ext-n8n"
        sa.save()
        mock_prov = _make_mock_provisioner("n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            reactivate_services(
                {"license_id": str(lic.id), "customer_id": str(customer.id)},
                str(uuid.uuid4()),
            )

        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.ACTIVE
        mock_prov.reactivate.assert_called_once()

    def test_skips_already_active_service_accesses(self):
        from apps.provisioning.handlers import reactivate_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        sa.status = ServiceAccess.Status.ACTIVE
        sa.save()
        mock_prov = _make_mock_provisioner("n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            reactivate_services(
                {"license_id": str(lic.id), "customer_id": str(customer.id)},
                str(uuid.uuid4()),
            )

        mock_prov.reactivate.assert_not_called()

    def test_early_return_when_no_license_id(self):
        from apps.provisioning.handlers import reactivate_services

        mock_prov = _make_mock_provisioner("n8n")
        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            reactivate_services(
                {"subscription_id": str(uuid.uuid4()), "customer_id": "cust-1"},
                str(uuid.uuid4()),
            )
        mock_prov.reactivate.assert_not_called()


# ---------------------------------------------------------------------------
# provision_single_service (service_access.provision)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProvisionSingleService:
    def test_provisions_and_marks_active(self):
        from apps.provisioning.handlers import provision_single_service

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        mock_prov = _make_mock_provisioner("n8n")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            provision_single_service(
                {
                    "service_access_id": str(sa.id),
                    "customer_id": str(customer.id),
                    "service_key": "n8n",
                },
                str(uuid.uuid4()),
            )

        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.ACTIVE
        assert sa.external_id == mock_prov.provision.return_value

    def test_marks_failed_on_exception(self):
        from apps.provisioning.handlers import provision_single_service

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        mock_prov = _make_mock_provisioner("n8n")
        mock_prov.provision.side_effect = RuntimeError("timeout")

        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            provision_single_service(
                {
                    "service_access_id": str(sa.id),
                    "customer_id": str(customer.id),
                    "service_key": "n8n",
                },
                str(uuid.uuid4()),
            )

        sa.refresh_from_db()
        assert sa.status == ServiceAccess.Status.FAILED
        assert "timeout" in sa.error

    def test_unknown_service_key_returns_early(self):
        from apps.provisioning.handlers import provision_single_service

        with patch("apps.provisioning.handlers.get_provisioner", return_value=None):
            provision_single_service(
                {
                    "service_access_id": str(uuid.uuid4()),
                    "customer_id": "cust-1",
                    "service_key": "unknown",
                },
                str(uuid.uuid4()),
            )

    def test_missing_service_access_returns_early(self):
        from apps.provisioning.handlers import provision_single_service

        mock_prov = _make_mock_provisioner("n8n")
        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            provision_single_service(
                {
                    "service_access_id": str(uuid.uuid4()),  # nonexistent
                    "customer_id": "cust-1",
                    "service_key": "n8n",
                },
                str(uuid.uuid4()),
            )
        mock_prov.provision.assert_not_called()


# ---------------------------------------------------------------------------
# deprovision_single_service (service_access.deprovision)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDeprovisionSingleService:
    def test_calls_provisioner_deprovision(self):
        from apps.provisioning.handlers import deprovision_single_service

        mock_prov = _make_mock_provisioner("n8n")
        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            deprovision_single_service(
                {
                    "service_key": "n8n",
                    "external_id": "ext-99",
                    "customer_id": "cust-1",
                },
                str(uuid.uuid4()),
            )

        mock_prov.deprovision.assert_called_once_with(external_id="ext-99", customer_id="cust-1")

    def test_unknown_service_key_returns_early(self):
        from apps.provisioning.handlers import deprovision_single_service

        with patch("apps.provisioning.handlers.get_provisioner", return_value=None):
            deprovision_single_service(
                {"service_key": "unknown", "external_id": "", "customer_id": "c1"},
                str(uuid.uuid4()),
            )

    def test_logs_error_and_continues_on_exception(self):
        from apps.provisioning.handlers import deprovision_single_service

        mock_prov = _make_mock_provisioner("n8n")
        mock_prov.deprovision.side_effect = RuntimeError("API error")
        with patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov):
            deprovision_single_service(
                {"service_key": "n8n", "external_id": "ext-1", "customer_id": "cust-1"},
                str(uuid.uuid4()),
            )
        mock_prov.deprovision.assert_called_once()


# ---------------------------------------------------------------------------
# sync_quota_on_create / sync_quota_on_renewal (_sync_quota)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSyncQuota:
    def test_creates_quota_on_subscription_created(self):
        from apps.licensing.models import LicenseQuota
        from apps.provisioning.handlers import sync_quota_on_create

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer)

        sync_quota_on_create({"subscription_id": str(sub.id)}, str(uuid.uuid4()))

        assert LicenseQuota.objects.filter(customer=customer).exists()

    def test_updates_quota_on_renewal(self):
        from apps.licensing.models import LicenseQuota
        from apps.provisioning.handlers import sync_quota_on_renewal

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer)
        LicenseQuota.objects.create(
            customer=customer,
            max_api_calls=999,
            used_api_calls=0,
            reset_at=timezone.now() + datetime.timedelta(days=30),
        )

        sync_quota_on_renewal({"subscription_id": str(sub.id)}, str(uuid.uuid4()))

        quota = LicenseQuota.objects.get(customer=customer)
        assert quota.max_api_calls == sub.pricing.max_api_calls

    def test_noop_when_subscription_id_missing(self):
        from apps.provisioning.handlers import sync_quota_on_create

        sync_quota_on_create({}, str(uuid.uuid4()))

    def test_noop_when_subscription_not_found(self):
        from apps.provisioning.handlers import sync_quota_on_create

        sync_quota_on_create({"subscription_id": str(uuid.uuid4())}, str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# cascade_suspend_subscriptions (customer.suspended)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCascadeSuspendSubscriptions:
    def test_suspends_active_subscriptions_of_customer(self):
        from apps.provisioning.handlers import cascade_suspend_subscriptions

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer)

        cascade_suspend_subscriptions({"customer_id": str(customer.id)}, str(uuid.uuid4()))

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.SUSPENDED

    def test_skips_cancelled_subscriptions(self):
        from apps.provisioning.handlers import cascade_suspend_subscriptions

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer)
        sub.status = Subscription.Status.CANCELLED
        sub.save()

        cascade_suspend_subscriptions({"customer_id": str(customer.id)}, str(uuid.uuid4()))

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.CANCELLED


# ---------------------------------------------------------------------------
# cascade_reactivate_subscriptions (customer.reactivated)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCascadeReactivateSubscriptions:
    def test_renews_suspended_subscriptions(self):
        from apps.provisioning.handlers import cascade_reactivate_subscriptions

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer)
        sub.status = Subscription.Status.SUSPENDED
        sub.save()

        cascade_reactivate_subscriptions({"customer_id": str(customer.id)}, str(uuid.uuid4()))

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.ACTIVE

    def test_skips_expired_subscriptions(self):
        from apps.provisioning.handlers import cascade_reactivate_subscriptions

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer)
        sub.status = Subscription.Status.EXPIRED
        sub.save()

        cascade_reactivate_subscriptions({"customer_id": str(customer.id)}, str(uuid.uuid4()))

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.EXPIRED


# ---------------------------------------------------------------------------
# notify_grace_period / notify_expiring_soon (task dispatch)
# ---------------------------------------------------------------------------


class TestNotifyHandlers:
    def test_notify_grace_period_dispatches_task(self):
        from apps.provisioning.handlers import notify_grace_period

        with patch("apps.notifications.tasks.send_subscription_grace_period_email") as mock_task:
            mock_task.delay = MagicMock()
            notify_grace_period({"subscription_id": "sub-1"}, "evt-1")
            mock_task.delay.assert_called_once_with("sub-1", "evt-1")

    def test_notify_expiring_soon_dispatches_task(self):
        from apps.provisioning.handlers import notify_expiring_soon

        with patch("apps.notifications.tasks.send_subscription_expiring_soon_email") as mock_task:
            mock_task.delay = MagicMock()
            notify_expiring_soon({"subscription_id": "sub-2"}, "evt-2")
            mock_task.delay.assert_called_once_with("sub-2", "evt-2")


# ---------------------------------------------------------------------------
# _emit_provisioned
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEmitProvisioned:
    def test_creates_outbox_event(self):
        from apps.provisioning.handlers import _emit_provisioned
        from shared.models import OutboxEvent

        customer_id = str(uuid.uuid4())
        _emit_provisioned(customer_id, "n8n")

        evt = OutboxEvent.objects.get(event_type="service.provisioned")
        assert evt.payload["customer_id"] == customer_id
        assert evt.payload["service_key"] == "n8n"
        assert evt.processed is False

    def test_emit_provisioned_called_on_success(self):
        from apps.provisioning.handlers import provision_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "chatwoot")
        mock_prov = _make_mock_provisioner("chatwoot")

        with (
            patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov),
            patch("apps.provisioning.handlers._emit_provisioned") as mock_emit,
        ):
            provision_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["chatwoot"],
                },
                str(uuid.uuid4()),
            )

        mock_emit.assert_called_once_with(str(customer.id), "chatwoot")

    def test_emit_provisioned_not_called_on_failure(self):
        from apps.provisioning.handlers import provision_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        mock_prov = _make_mock_provisioner("n8n")
        mock_prov.provision.side_effect = RuntimeError("Timeout")

        with (
            patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov),
            patch("apps.provisioning.handlers._emit_provisioned") as mock_emit,
        ):
            provision_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )

        mock_emit.assert_not_called()


# ---------------------------------------------------------------------------
# _alert_telegram
# ---------------------------------------------------------------------------


class TestAlertTelegram:
    def test_noop_when_token_not_configured(self):
        from apps.provisioning.handlers import _alert_telegram

        # Default settings have empty token so requests.post must not be called
        with patch("requests.post") as mock_post:
            _alert_telegram("test message")
            mock_post.assert_not_called()

    def test_calls_telegram_api_when_configured(self):
        from django.test import override_settings

        from apps.provisioning.handlers import _alert_telegram

        with (
            override_settings(
                TELEGRAM_BOT_TOKEN="bot-token-123", TELEGRAM_ALERT_CHAT_ID="chat-456"
            ),
            patch("requests.post") as mock_post,
        ):
            _alert_telegram("<b>Alert</b>")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "bot-token-123" in url

    @pytest.mark.django_db
    def test_telegram_alert_sent_on_provision_failure(self):
        from apps.provisioning.handlers import provision_services

        customer = _make_customer()
        sub, lic, sa = _make_subscription_with_sa(customer, "n8n")
        mock_prov = _make_mock_provisioner("n8n")
        mock_prov.provision.side_effect = RuntimeError("Server 500")

        with (
            patch("apps.provisioning.handlers.get_provisioner", return_value=mock_prov),
            patch("apps.provisioning.handlers._alert_telegram") as mock_alert,
        ):
            provision_services(
                {
                    "license_id": str(lic.id),
                    "customer_id": str(customer.id),
                    "service_keys": ["n8n"],
                },
                str(uuid.uuid4()),
            )

        mock_alert.assert_called_once()
        alert_msg = mock_alert.call_args[0][0]
        assert "n8n" in alert_msg
        assert "Server 500" in alert_msg
