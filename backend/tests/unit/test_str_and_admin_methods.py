"""
Micro-tests for __str__, simple admin actions, and renderer/exception edge cases.

Each class targets a single file/class that was measured < 100% by coverage.
No external services; most classes need no DB (no @pytest.mark.django_db).
"""

import datetime
import decimal
from unittest.mock import MagicMock, patch
import uuid

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
import pytest

# ---------------------------------------------------------------------------
# shared/renderers.py line 20 — _ExtendedEncoder.default() fallback
# ---------------------------------------------------------------------------


class TestExtendedEncoderFallback:
    def test_raises_for_unrecognised_type(self):
        """super().default() raises TypeError for unknown objects — confirms the fallback fires."""
        from shared.renderers import _ExtendedEncoder

        encoder = _ExtendedEncoder()
        with pytest.raises(TypeError):
            encoder.default(object())  # plain object is not serialisable

    def test_uuid_serialises_to_str(self):
        from shared.renderers import _ExtendedEncoder

        uid = uuid.uuid4()
        assert _ExtendedEncoder().default(uid) == str(uid)

    def test_decimal_serialises_to_str(self):
        from shared.renderers import _ExtendedEncoder

        assert _ExtendedEncoder().default(decimal.Decimal("9.99")) == "9.99"

    def test_date_serialises_to_isoformat(self):
        from shared.renderers import _ExtendedEncoder

        d = datetime.date(2026, 1, 15)
        assert _ExtendedEncoder().default(d) == "2026-01-15"


# ---------------------------------------------------------------------------
# shared/exceptions.py lines 57-58 — else branch (detail is neither dict nor list)
# ---------------------------------------------------------------------------


class TestCustomExceptionHandlerStringDetail:
    def test_string_detail_becomes_message(self):
        from rest_framework.exceptions import PermissionDenied

        from shared.exceptions import custom_exception_handler

        mock_response = MagicMock()
        mock_response.data = "plain string detail"
        mock_response.status_code = 403

        with patch("rest_framework.views.exception_handler", return_value=mock_response):
            result = custom_exception_handler(PermissionDenied("test"), {})

        assert result is not None
        assert result.data["message"] == "plain string detail"
        assert result.data["details"] == []

    def test_none_response_returns_none(self):
        """When the default handler returns None, the custom handler propagates None."""
        from shared.exceptions import custom_exception_handler

        with patch("rest_framework.views.exception_handler", return_value=None):
            result = custom_exception_handler(RuntimeError("unhandled"), {})

        assert result is None


# ---------------------------------------------------------------------------
# shared/admin.py line 22 — OutboxEventAdmin.has_add_permission
# ---------------------------------------------------------------------------


class TestOutboxEventAdminPermissions:
    def test_has_add_permission_returns_false(self):
        from shared.admin import OutboxEventAdmin
        from shared.models import OutboxEvent

        admin_obj = OutboxEventAdmin(OutboxEvent, AdminSite())
        assert admin_obj.has_add_permission(MagicMock()) is False


# ---------------------------------------------------------------------------
# customers/admin.py lines 24, 28 — mark_suspended / mark_active
# ---------------------------------------------------------------------------


def _admin_request(user):
    factory = RequestFactory()
    req = factory.get("/")
    req.user = user
    req.session = "session"
    req._messages = FallbackStorage(req)
    return req


@pytest.mark.django_db
class TestCustomerAdminActions:
    def test_mark_suspended_updates_queryset(self, admin_user, customer):
        from apps.customers.admin import CustomerAdmin
        from apps.customers.models import Customer

        site = AdminSite()
        admin_obj = CustomerAdmin(Customer, site)
        qs = Customer.objects.filter(id=customer.id)
        admin_obj.mark_suspended(_admin_request(admin_user), qs)

        customer.refresh_from_db()
        assert customer.status == Customer.Status.SUSPENDED

    def test_mark_active_updates_queryset(self, admin_user, customer):
        from apps.customers.admin import CustomerAdmin
        from apps.customers.models import Customer

        # Start from a suspended state
        customer.status = Customer.Status.SUSPENDED
        customer.save()

        site = AdminSite()
        admin_obj = CustomerAdmin(Customer, site)
        qs = Customer.objects.filter(id=customer.id)
        admin_obj.mark_active(_admin_request(admin_user), qs)

        customer.refresh_from_db()
        assert customer.status == Customer.Status.ACTIVE


# ---------------------------------------------------------------------------
# licensing/admin.py line 15 — ApiKeyAdmin.key_preview
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestApiKeyAdminKeyPreview:
    def test_key_preview_returns_first_eight_chars(self, api_key):
        from apps.licensing.admin import ApiKeyAdmin
        from apps.licensing.models import ApiKey

        site = AdminSite()
        admin_obj = ApiKeyAdmin(ApiKey, site)
        preview = admin_obj.key_preview(api_key)

        assert preview.startswith(api_key.key[:8])
        assert "…" in preview


# ---------------------------------------------------------------------------
# Model __str__ methods (no DB required — just instantiate)
# ---------------------------------------------------------------------------


class TestModelStrMethods:
    # customers/models.py line 31
    def test_customer_str(self):
        from apps.customers.models import Customer

        c = Customer(company_name="Acme Ltda")
        assert str(c) == "Acme Ltda"

    # customers/models.py line 87
    def test_invitation_str(self):
        from apps.customers.models import Invitation

        inv = Invitation(email="test@x.com", status="pending")
        text = str(inv)
        assert "test@x.com" in text
        assert "pending" in text

    # customers/models.py line 118
    def test_customer_profile_str(self):
        from apps.customers.models import CustomerProfile

        prof = CustomerProfile(customer_id=uuid.uuid4(), role="owner")
        text = str(prof)
        assert "owner" in text

    # licensing/models.py line 23
    def test_api_key_str(self):
        from apps.licensing.models import ApiKey

        k = ApiKey(customer_id=uuid.uuid4(), is_active=True)
        text = str(k)
        assert "ApiKey" in text

    # licensing/models.py line 45
    def test_license_quota_str(self):
        from apps.licensing.models import LicenseQuota

        q = LicenseQuota(customer_id=uuid.uuid4(), used_api_calls=50, max_api_calls=100)
        text = str(q)
        assert "50/100" in text

    # products/models.py line 19
    def test_product_str(self):
        from apps.products.models import Product

        p = Product(name="PaperMoon Suite")
        assert str(p) == "PaperMoon Suite"

    # products/models.py line 45 (ServiceComponent needs a related Product)
    def test_service_component_str(self):
        from apps.products.models import Product, ServiceComponent

        prod = Product(name="Suite")
        sc = ServiceComponent(product=prod, service_key="n8n")
        text = str(sc)
        assert "Suite" in text
        assert "n8n" in text

    # products/models.py line 69 (Pricing needs a related Product)
    def test_pricing_str(self):
        from apps.products.models import Pricing, Product

        prod = Product(name="Suite")
        pr = Pricing(product=prod, billing_cycle="monthly", amount=decimal.Decimal("99.00"))
        text = str(pr)
        assert "Suite" in text
        assert "monthly" in text
        assert "99" in text

    # subscriptions/models.py line 93 (License)
    def test_license_str(self):
        from apps.subscriptions.models import License

        lic = License(subscription_id=uuid.uuid4(), status="active")
        text = str(lic)
        assert "active" in text

    # subscriptions/models.py line 137 (ServiceAccess)
    def test_service_access_str(self):
        from apps.subscriptions.models import ServiceAccess

        sa = ServiceAccess(license_id=uuid.uuid4(), service_key="n8n", status="active")
        text = str(sa)
        assert "n8n" in text
        assert "active" in text

    # billing/models.py line 46 — is_deleted property
    def test_invoice_is_deleted_false_when_deleted_at_none(self):
        from apps.billing.models import Invoice

        inv = Invoice(deleted_at=None)
        assert inv.is_deleted is False

    def test_invoice_is_deleted_true_when_deleted_at_set(self):
        from apps.billing.models import Invoice

        inv = Invoice(deleted_at=datetime.datetime.now(tz=datetime.UTC))
        assert inv.is_deleted is True

    # notifications/models.py line 45
    def test_notification_str(self):
        from apps.notifications.models import Notification

        n = Notification(
            event_type="payment.failed", channel="email", recipient="a@b.com", status="sent"
        )
        text = str(n)
        assert "payment.failed" in text
        assert "email" in text
        assert "a@b.com" in text


# ---------------------------------------------------------------------------
# notifications/registry.py line 25 — registered_event_types()
# ---------------------------------------------------------------------------


class TestNotificationsRegistry:
    def test_registered_event_types_returns_list(self):
        from apps.notifications.registry import registered_event_types

        result = registered_event_types()
        assert isinstance(result, list)
        # At least some handlers are registered (email, in-app, etc.)
        assert len(result) > 0

    def test_registered_event_types_contains_known_events(self):
        from apps.notifications.registry import registered_event_types

        types = registered_event_types()
        # payment.processed and subscription.suspended are always registered
        assert "payment.processed" in types or "subscription.suspended" in types


# ---------------------------------------------------------------------------
# subscriptions/models.py line 53 — transition_to() successful save
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSubscriptionTransitionToSave:
    def test_transition_to_saves_new_status(self, customer):
        from apps.products.models import Pricing, Product
        from apps.subscriptions.models import Subscription

        slug = f"trans-{uuid.uuid4().hex[:8]}"
        product = Product.objects.create(name=f"P {slug}", slug=slug)
        pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
        sub = Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=datetime.datetime.now(tz=datetime.UTC),
            expires_at=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=30),
        )

        sub.transition_to(Subscription.Status.GRACE_PERIOD)

        sub.refresh_from_db()
        assert sub.status == Subscription.Status.GRACE_PERIOD

    def test_subscription_str(self, customer):
        from apps.products.models import Pricing, Product
        from apps.subscriptions.models import Subscription

        slug = f"str-{uuid.uuid4().hex[:8]}"
        product = Product.objects.create(name=f"P {slug}", slug=slug)
        pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
        sub = Subscription.objects.create(
            customer=customer,
            product=product,
            pricing=pricing,
            status=Subscription.Status.ACTIVE,
            starts_at=datetime.datetime.now(tz=datetime.UTC),
            expires_at=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=30),
        )

        text = str(sub)
        assert "active" in text


# ---------------------------------------------------------------------------
# customers/commands.py lines 37-38 — NotFound for missing customer
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateInvitationCommandNotFound:
    def test_raises_not_found_for_nonexistent_customer(self, regular_user):
        from rest_framework.exceptions import NotFound

        from apps.customers.commands import CreateInvitationCommand

        cmd = CreateInvitationCommand(
            customer_id=uuid.uuid4(),
            email="invite@x.com",
            role="member",
            invited_by_id=regular_user.id,
        )
        with pytest.raises(NotFound):
            cmd.execute()
