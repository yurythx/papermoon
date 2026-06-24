"""
Shared fixtures for the entire test suite.

Unit tests: use `repo` + `service` fixtures (mocked, no DB).
Integration tests: use `api_client`, `admin_client`, `customer_client` (real DB via pytest-django).
"""

import datetime
from unittest.mock import MagicMock

from django.utils import timezone
import pytest
from rest_framework.test import APIClient


def create_active_license(customer):
    """
    Creates the minimal Product → Pricing → Subscription → License chain for a customer.
    Used by fixtures that need validate-key to return valid=True.
    """
    from uuid import uuid4

    from apps.products.models import Pricing, Product
    from apps.subscriptions.models import License, Subscription

    product = Product.objects.create(name="Test Product", slug=f"test-{uuid4().hex[:8]}")
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="99.00")
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now() + datetime.timedelta(days=30),
    )
    return License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + datetime.timedelta(days=30),
    )


# ---------------------------------------------------------------------------
# HTTP clients
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    from apps.accounts.models import CustomUser

    return CustomUser.objects.create_superuser(
        username="admin",
        email="admin@papermoon.com",
        password="admin123",
    )


@pytest.fixture
def regular_user(db):
    from apps.accounts.models import CustomUser

    return CustomUser.objects.create_user(
        username="user",
        email="user@papermoon.com",
        password="user123",
    )


def _login(client, email, password):
    resp = client.post(
        "/api/v1/auth/login/",
        {"email": email, "password": password},
        format="json",
    )
    token = resp.json()["data"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def admin_client(api_client, admin_user):
    return _login(api_client, "admin@papermoon.com", "admin123")


@pytest.fixture
def customer_client(api_client, regular_user, customer_with_profile):
    return _login(api_client, "user@papermoon.com", "user123")


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------


@pytest.fixture
def customer(db):
    from apps.customers.models import Customer

    return Customer.objects.create(
        company_name="Empresa Teste",
        document="11.222.333/0001-81",
    )


@pytest.fixture
def customer_with_profile(db, regular_user):
    from apps.customers.models import Customer, CustomerProfile

    c = Customer.objects.create(
        company_name="Empresa Cliente",
        document="98.765.432/0001-98",
    )
    CustomerProfile.objects.create(user=regular_user, customer=c, role="owner")
    return c


@pytest.fixture
def invoice(db, customer):
    from apps.billing.models import Invoice

    return Invoice.objects.create(
        customer=customer,
        amount="500.00",
        due_date=datetime.date.today(),
    )


@pytest.fixture
def api_key(db, customer):
    from apps.licensing.models import ApiKey, LicenseQuota

    key = ApiKey.objects.create(customer=customer)
    LicenseQuota.objects.create(
        customer=customer,
        max_api_calls=1000,
        used_api_calls=0,
        reset_at=datetime.datetime(2099, 1, 1, tzinfo=datetime.UTC),
    )
    create_active_license(customer)
    return key


# ---------------------------------------------------------------------------
# Unit-test repo mock
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    return MagicMock()
