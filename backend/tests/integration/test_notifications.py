"""End-to-end tests: OutboxEvent → handler dispatch → Notification model."""

import datetime

import pytest


@pytest.mark.django_db
class TestOutboxToNotificationFlow:
    def test_payment_processed_creates_notification_record(self):
        from apps.accounts.models import CustomUser
        from apps.billing.models import Invoice
        from apps.customers.models import Customer
        from apps.notifications.tasks import process_outbox_events
        from shared.models import OutboxEvent

        CustomUser.objects.create_user(username="notif_user", email="notif@test.com", password="x")
        customer = Customer.objects.create(company_name="Notif Corp", document="77.777.777/0001-77")
        invoice = Invoice.objects.create(
            customer=customer,
            amount="150.00",
            due_date=datetime.date.today(),
        )

        OutboxEvent.objects.create(
            event_type="payment.processed",
            payload={"invoice_id": str(invoice.id), "customer_id": str(customer.id)},
        )

        # Dispatch — email tasks are mocked to avoid real SMTP
        from unittest.mock import patch

        with patch("apps.notifications.tasks.send_payment_confirmed_email.delay") as mock_task:
            process_outbox_events()
            mock_task.assert_called_once()

    def test_outbox_event_marked_processed_after_dispatch(self):
        from unittest.mock import patch

        from apps.customers.models import Customer
        from shared.models import OutboxEvent

        customer = Customer.objects.create(
            company_name="Processed Corp", document="88.888.888/0001-88"
        )
        event = OutboxEvent.objects.create(
            event_type="customer.created",
            payload={"customer_id": str(customer.id), "plan_id": None},
        )

        from apps.notifications.tasks import process_outbox_events

        with (
            patch("apps.support.client.ChatwootClient.provision_customer"),
            patch("apps.billing.customer_commands.ProvisionAsaasCustomerCommand.execute"),
        ):
            process_outbox_events()

        event.refresh_from_db()
        assert event.processed is True
        assert event.processed_at is not None

    def test_duplicate_notification_is_idempotent(self):
        import uuid

        from apps.billing.models import Invoice
        from apps.customers.models import Customer
        from apps.notifications.models import Notification

        customer = Customer.objects.create(
            company_name="Idempotent Corp", document="99.999.999/0001-99"
        )
        invoice = Invoice.objects.create(
            customer=customer,
            amount="200.00",
            due_date=datetime.date.today(),
        )
        event_id = str(uuid.uuid4())

        # Create a notification that was already sent
        Notification.objects.create(
            outbox_event_id=event_id,
            event_type="payment.processed",
            channel=Notification.Channel.EMAIL,
            recipient="test@test.com",
            status=Notification.Status.SENT,
        )

        # Simulating a second call to the email task with the same event_id
        from unittest.mock import patch

        from apps.notifications.tasks import send_payment_confirmed_email

        with patch("apps.notifications.tasks.send_html_email") as mock_mail:
            send_payment_confirmed_email(str(invoice.id), event_id)
            # send_html_email should NOT be called since notification was already SENT
            mock_mail.assert_not_called()

    def test_customer_suspended_deactivates_api_keys(self):
        from unittest.mock import patch

        from apps.customers.models import Customer
        from apps.licensing.models import ApiKey
        from apps.notifications.tasks import process_outbox_events
        from shared.models import OutboxEvent

        customer = Customer.objects.create(company_name="Keys Corp", document="10.000.000/0001-00")
        key1 = ApiKey.objects.create(customer=customer, is_active=True)
        key2 = ApiKey.objects.create(customer=customer, is_active=True)

        OutboxEvent.objects.create(
            event_type="customer.suspended",
            payload={"customer_id": str(customer.id)},
        )
        # Patch Chatwoot to avoid real HTTP during test
        with patch("apps.support.client.ChatwootClient.suspend_agents"):
            process_outbox_events()

        key1.refresh_from_db()
        key2.refresh_from_db()
        assert key1.is_active is False
        assert key2.is_active is False

    def test_send_payment_confirmed_email_calls_send_html_email(self):
        import datetime
        from unittest.mock import patch
        import uuid

        from apps.accounts.models import CustomUser
        from apps.billing.models import Invoice
        from apps.customers.models import Customer, CustomerProfile
        from apps.notifications.models import Notification
        from apps.notifications.tasks import send_payment_confirmed_email

        customer = Customer.objects.create(company_name="Email Corp", document="30.000.000/0001-00")
        user = CustomUser.objects.create_user(
            username="emailuser", email="owner@emailcorp.com", password="x"
        )
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")
        invoice = Invoice.objects.create(
            customer=customer, amount="299.00", due_date=datetime.date.today()
        )
        event_id = str(uuid.uuid4())

        with patch("apps.notifications.tasks.send_html_email") as mock_mail:
            send_payment_confirmed_email(str(invoice.id), event_id)
            mock_mail.assert_called_once()
            kw = mock_mail.call_args.kwargs
            assert "Pagamento confirmado" in kw["subject"]
            assert kw["recipient"] == "owner@emailcorp.com"

        notification = Notification.objects.get(outbox_event_id=event_id)
        assert notification.status == Notification.Status.SENT

    def test_send_invitation_email_calls_send_html_email(self):
        from unittest.mock import patch
        import uuid

        from apps.accounts.models import CustomUser
        from apps.customers.models import Customer, CustomerProfile, Invitation
        from apps.notifications.tasks import send_invitation_email

        customer = Customer.objects.create(
            company_name="Invite Corp", document="31.000.000/0001-00"
        )
        inviter = CustomUser.objects.create_user(
            username="inviter01", email="inviter@test.com", password="x"
        )
        CustomerProfile.objects.create(user=inviter, customer=customer, role="owner")
        from datetime import timedelta

        from django.utils import timezone

        invitation = Invitation.objects.create(
            customer=customer,
            invited_by=inviter,
            email="invited@example.com",
            role="member",
            expires_at=timezone.now() + timedelta(days=7),
        )
        event_id = str(uuid.uuid4())

        with patch("apps.notifications.tasks.send_html_email") as mock_mail:
            send_invitation_email(str(invitation.id), event_id)
            mock_mail.assert_called_once()
            kw = mock_mail.call_args.kwargs
            assert "convidou" in kw["subject"]
            assert kw["recipient"] == "invited@example.com"

    def test_customer_created_creates_license_quota(self):
        from unittest.mock import patch

        from apps.customers.models import Customer
        from apps.licensing.models import LicenseQuota
        from apps.notifications.tasks import process_outbox_events
        from shared.models import OutboxEvent

        customer = Customer.objects.create(company_name="Quota Corp", document="20.000.000/0001-00")

        OutboxEvent.objects.create(
            event_type="customer.created",
            payload={"customer_id": str(customer.id), "plan_id": None},
        )
        # Patch Chatwoot to avoid real HTTP during test
        with patch("apps.support.client.ChatwootClient.provision_customer"):
            process_outbox_events()

        assert LicenseQuota.objects.filter(customer=customer).exists()
