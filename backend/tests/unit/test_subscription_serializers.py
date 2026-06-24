"""
Unit tests for SubscriptionSerializer and ServiceAccessSerializer.

Uses mock objects — no DB required.
Covers:
  - customer_id / customer_name (added after initial implementation)
  - service_url mapping from Django settings via ServiceAccessSerializer
  - LicenseClientSerializer.days_remaining edge cases
"""

import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from django.utils import timezone

# ---------------------------------------------------------------------------
# Helpers: build minimal mock objects that satisfy serializer source traversal
# ---------------------------------------------------------------------------


def _make_customer(name="Empresa Teste"):
    c = SimpleNamespace()
    c.id = uuid4()
    c.company_name = name
    return c


def _make_product():
    p = SimpleNamespace()
    p.id = uuid4()
    p.name = "Plano Starter"
    p.slug = "starter"
    return p


def _make_pricing(cycle="monthly", amount="199.00"):
    pr = SimpleNamespace()
    pr.id = uuid4()
    pr.billing_cycle = cycle
    pr.amount = Decimal(amount)
    return pr


def _make_license(valid_until=None):
    lic = MagicMock()
    lic.id = uuid4()
    lic.key = "LIC-TEST-KEY"
    lic.status = "active"
    lic.valid_from = timezone.now()
    lic.valid_until = valid_until or (timezone.now() + datetime.timedelta(days=30))
    lic.created_at = timezone.now()
    lic.service_accesses.all.return_value = []
    return lic


def _make_subscription(customer=None, with_license=False):
    customer = customer or _make_customer()
    product = _make_product()
    pricing = _make_pricing()
    sub = SimpleNamespace()
    sub.id = uuid4()
    sub.status = "active"
    sub.customer = customer
    sub.product = product
    sub.pricing = pricing
    sub.starts_at = timezone.now()
    sub.expires_at = timezone.now() + datetime.timedelta(days=30)
    sub.created_at = timezone.now()
    sub.updated_at = timezone.now()
    sub.license = _make_license() if with_license else None
    return sub


def _make_service_access(service_key="chatwoot"):
    sa = SimpleNamespace()
    sa.id = uuid4()
    sa.license_id = uuid4()
    sa.service_key = service_key
    sa.status = "active"
    sa.external_id = None
    sa.config = {}
    sa.provisioned_at = None
    sa.suspended_at = None
    sa.error = None
    sa.created_at = timezone.now()
    sa.updated_at = timezone.now()
    return sa


# ---------------------------------------------------------------------------
# SubscriptionSerializer — customer_id / customer_name
# ---------------------------------------------------------------------------


def test_subscription_serializer_customer_id():
    from apps.subscriptions.serializers import SubscriptionSerializer

    customer = _make_customer()
    sub = _make_subscription(customer=customer)
    data = SubscriptionSerializer(sub).data
    assert str(data["customer_id"]) == str(customer.id)


def test_subscription_serializer_customer_name():
    from apps.subscriptions.serializers import SubscriptionSerializer

    customer = _make_customer("Acme Ltda")
    sub = _make_subscription(customer=customer)
    data = SubscriptionSerializer(sub).data
    assert data["customer_name"] == "Acme Ltda"


def test_subscription_serializer_product_fields():
    from apps.subscriptions.serializers import SubscriptionSerializer

    sub = _make_subscription()
    data = SubscriptionSerializer(sub).data
    assert str(data["product_id"]) == str(sub.product.id)
    assert data["product_name"] == "Plano Starter"
    assert data["product_slug"] == "starter"


def test_subscription_serializer_pricing_fields():
    from apps.subscriptions.serializers import SubscriptionSerializer

    sub = _make_subscription()
    data = SubscriptionSerializer(sub).data
    assert str(data["pricing_id"]) == str(sub.pricing.id)
    assert data["billing_cycle"] == "monthly"
    assert data["amount"] == "199.00"


def test_subscription_serializer_license_null_when_absent():
    from apps.subscriptions.serializers import SubscriptionSerializer

    sub = _make_subscription(with_license=False)
    data = SubscriptionSerializer(sub).data
    assert data["license"] is None


def test_subscription_serializer_status():
    from apps.subscriptions.serializers import SubscriptionSerializer

    sub = _make_subscription()
    sub.status = "suspended"
    data = SubscriptionSerializer(sub).data
    assert data["status"] == "suspended"


# ---------------------------------------------------------------------------
# ServiceAccessSerializer — service_url
# ---------------------------------------------------------------------------


def test_service_access_serializer_chatwoot_url(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    settings.CHATWOOT_API_URL = "https://chat.example.com"
    sa = _make_service_access("chatwoot")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] == "https://chat.example.com"


def test_service_access_serializer_n8n_url(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    settings.N8N_API_URL = "https://n8n.example.com"
    sa = _make_service_access("n8n")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] == "https://n8n.example.com"


def test_service_access_serializer_glpi_url(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    settings.GLPI_API_URL = "https://glpi.example.com"
    sa = _make_service_access("glpi")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] == "https://glpi.example.com"


def test_service_access_serializer_zabbix_url(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    settings.ZABBIX_API_URL = "https://zabbix.example.com"
    sa = _make_service_access("zabbix")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] == "https://zabbix.example.com"


def test_service_access_serializer_empty_setting_returns_none(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    settings.GLPI_API_URL = ""
    sa = _make_service_access("glpi")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] is None


def test_service_access_serializer_unknown_key_returns_none():
    from apps.subscriptions.serializers import ServiceAccessSerializer

    sa = _make_service_access("meta_whatsapp")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] is None


def test_service_access_serializer_missing_setting_attr_returns_none(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    if hasattr(settings, "N8N_API_URL"):
        delattr(settings, "N8N_API_URL")
    sa = _make_service_access("n8n")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] is None


def test_service_access_serializer_allows_localhost_for_dev(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    settings.N8N_API_URL = "http://localhost:5678"
    sa = _make_service_access("n8n")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] == "http://localhost:5678"


def test_service_access_serializer_rejects_private_network_url(settings):
    from apps.subscriptions.serializers import ServiceAccessSerializer

    settings.N8N_API_URL = "http://10.0.0.20:5678"
    sa = _make_service_access("n8n")
    data = ServiceAccessSerializer(sa).data
    assert data["service_url"] is None


# ---------------------------------------------------------------------------
# LicenseClientSerializer — days_remaining
# ---------------------------------------------------------------------------


def test_license_client_serializer_days_remaining():
    from apps.subscriptions.serializers import LicenseClientSerializer

    lic = _make_license(valid_until=timezone.now() + datetime.timedelta(days=15))
    lic.subscription.product.name = "Plano Starter"
    lic.subscription.product.slug = "starter"
    lic.subscription.id = uuid4()
    lic.subscription.status = "active"
    lic.subscription.pricing.billing_cycle = "monthly"
    lic.subscription.pricing.amount = Decimal("199.00")

    data = LicenseClientSerializer(lic).data
    assert 14 <= data["days_remaining"] <= 15


def test_license_client_serializer_days_remaining_zero_when_expired():
    from apps.subscriptions.serializers import LicenseClientSerializer

    past = timezone.now() - datetime.timedelta(days=5)
    lic = _make_license(valid_until=past)
    lic.subscription.product.name = "Plano Starter"
    lic.subscription.product.slug = "starter"
    lic.subscription.id = uuid4()
    lic.subscription.status = "expired"
    lic.subscription.pricing.billing_cycle = "monthly"
    lic.subscription.pricing.amount = Decimal("199.00")

    data = LicenseClientSerializer(lic).data
    assert data["days_remaining"] == 0
