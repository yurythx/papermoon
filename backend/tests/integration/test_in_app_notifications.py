"""Integration tests for in-app notification endpoints."""

import pytest


@pytest.mark.django_db
class TestInAppNotificationList:
    def test_returns_empty_list_when_no_notifications(self, customer_client):
        resp = customer_client.get("/api/v1/client/notifications/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["count"] == 0
        assert data["unread_count"] == 0
        assert data["results"] == []

    def test_returns_notifications_for_authenticated_customer(
        self, customer_client, customer_with_profile
    ):
        from apps.notifications.models import Notification

        Notification.objects.create(
            event_type="payment.processed",
            channel=Notification.Channel.IN_APP,
            recipient=str(customer_with_profile.id),
            subject="Pagamento confirmado",
            body="Fatura paga.",
            status=Notification.Status.PENDING,
        )

        resp = customer_client.get("/api/v1/client/notifications/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["count"] == 1
        assert data["unread_count"] == 1
        assert data["results"][0]["subject"] == "Pagamento confirmado"
        assert data["results"][0]["is_read"] is False

    def test_does_not_return_other_customers_notifications(
        self, customer_client, customer_with_profile
    ):
        from apps.customers.models import Customer
        from apps.notifications.models import Notification

        other = Customer.objects.create(company_name="Outra Empresa", document="11.111.111/0001-11")
        Notification.objects.create(
            event_type="payment.failed",
            channel=Notification.Channel.IN_APP,
            recipient=str(other.id),
            subject="Fatura vencida",
            body="Regularize.",
            status=Notification.Status.PENDING,
        )

        resp = customer_client.get("/api/v1/client/notifications/")
        assert resp.status_code == 200
        assert resp.json()["data"]["count"] == 0

    def test_requires_authentication(self, api_client):
        resp = api_client.get("/api/v1/client/notifications/")
        assert resp.status_code == 401

    def test_unread_count_excludes_already_read(self, customer_client, customer_with_profile):
        from django.utils import timezone

        from apps.notifications.models import Notification

        Notification.objects.create(
            event_type="payment.processed",
            channel=Notification.Channel.IN_APP,
            recipient=str(customer_with_profile.id),
            subject="Lida",
            body=".",
            status=Notification.Status.SENT,
            sent_at=timezone.now(),
        )
        Notification.objects.create(
            event_type="payment.failed",
            channel=Notification.Channel.IN_APP,
            recipient=str(customer_with_profile.id),
            subject="Não lida",
            body=".",
            status=Notification.Status.PENDING,
        )

        resp = customer_client.get("/api/v1/client/notifications/")
        data = resp.json()["data"]
        assert data["count"] == 2
        assert data["unread_count"] == 1


@pytest.mark.django_db
class TestMarkNotificationRead:
    def test_marks_single_notification_as_read(self, customer_client, customer_with_profile):
        from apps.notifications.models import Notification

        n = Notification.objects.create(
            event_type="payment.processed",
            channel=Notification.Channel.IN_APP,
            recipient=str(customer_with_profile.id),
            subject="Pagamento confirmado",
            body=".",
            status=Notification.Status.PENDING,
        )

        resp = customer_client.post(f"/api/v1/client/notifications/{n.id}/read/")
        assert resp.status_code == 200

        n.refresh_from_db()
        assert n.status == Notification.Status.SENT
        assert n.sent_at is not None

    def test_idempotent_if_already_read(self, customer_client, customer_with_profile):
        from django.utils import timezone

        from apps.notifications.models import Notification

        original_read_at = timezone.now()
        n = Notification.objects.create(
            event_type="payment.processed",
            channel=Notification.Channel.IN_APP,
            recipient=str(customer_with_profile.id),
            subject="Já lida",
            body=".",
            status=Notification.Status.SENT,
            sent_at=original_read_at,
        )

        resp = customer_client.post(f"/api/v1/client/notifications/{n.id}/read/")
        assert resp.status_code == 200
        n.refresh_from_db()
        assert n.sent_at == original_read_at  # unchanged

    def test_returns_404_for_other_customers_notification(
        self, customer_client, customer_with_profile
    ):
        from apps.customers.models import Customer
        from apps.notifications.models import Notification

        other = Customer.objects.create(company_name="Outra Empresa", document="22.222.222/0002-22")
        n = Notification.objects.create(
            event_type="payment.processed",
            channel=Notification.Channel.IN_APP,
            recipient=str(other.id),
            subject="Não é sua",
            body=".",
            status=Notification.Status.PENDING,
        )

        resp = customer_client.post(f"/api/v1/client/notifications/{n.id}/read/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestMarkAllNotificationsRead:
    def test_marks_all_unread_as_read(self, customer_client, customer_with_profile):
        from apps.notifications.models import Notification

        for i in range(3):
            Notification.objects.create(
                event_type="payment.processed",
                channel=Notification.Channel.IN_APP,
                recipient=str(customer_with_profile.id),
                subject=f"Notif {i}",
                body=".",
                status=Notification.Status.PENDING,
            )

        resp = customer_client.post("/api/v1/client/notifications/read-all/")
        assert resp.status_code == 200

        unread = Notification.objects.filter(
            recipient=str(customer_with_profile.id),
            status=Notification.Status.PENDING,
        ).count()
        assert unread == 0

    def test_does_not_touch_other_customers_notifications(
        self, customer_client, customer_with_profile
    ):
        from apps.customers.models import Customer
        from apps.notifications.models import Notification

        other = Customer.objects.create(company_name="Outra", document="33.333.333/0003-33")
        n = Notification.objects.create(
            event_type="payment.failed",
            channel=Notification.Channel.IN_APP,
            recipient=str(other.id),
            subject="Outra empresa",
            body=".",
            status=Notification.Status.PENDING,
        )

        customer_client.post("/api/v1/client/notifications/read-all/")

        n.refresh_from_db()
        assert n.status == Notification.Status.PENDING  # untouched
