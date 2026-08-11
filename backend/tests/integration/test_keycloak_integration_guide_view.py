"""Integration tests for apps/subscriptions/views_client.py::ClientKeycloakIntegrationGuideView."""

from unittest.mock import MagicMock, patch
import uuid

import pytest

from apps.customers.models import Customer
from apps.products.models import Pricing, Product, ServiceComponent
from apps.subscriptions.models import License, ServiceAccess, Subscription

BASE_URL = "/api/v1/client/subscriptions/keycloak-integration-guide/"


def _make_keycloak_service_access(customer: Customer, *, external_id: str = "tenant-abc123"):
    import datetime

    from django.utils import timezone

    product = Product.objects.create(name="Keycloak Product", slug=f"kc-{uuid.uuid4().hex[:6]}")
    ServiceComponent.objects.create(product=product, service_key="keycloak")
    pricing = Pricing.objects.create(product=product, billing_cycle="monthly", amount="199.00")
    sub = Subscription.objects.create(
        customer=customer,
        product=product,
        pricing=pricing,
        status=Subscription.Status.ACTIVE,
        starts_at=timezone.now(),
        expires_at=timezone.now() + datetime.timedelta(days=30),
    )
    license_obj = License.objects.create(
        subscription=sub,
        customer=customer,
        key=License.generate_key(),
        status=License.Status.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + datetime.timedelta(days=30),
    )
    return ServiceAccess.objects.create(
        license=license_obj,
        service_key="keycloak",
        status=ServiceAccess.Status.ACTIVE,
        external_id=external_id,
    )


def _query(**overrides):
    params = {
        "language": "nextjs",
        "app_name": "Minha App",
        "base_url": "https://meusistema.com.br",
    }
    params.update(overrides)
    return params


@pytest.mark.django_db
class TestClientKeycloakIntegrationGuideView:
    def test_returns_not_available_without_active_keycloak_service_access(
        self, customer_client, customer_with_profile, settings
    ):
        settings.KEYCLOAK_API_URL = "https://keycloak.example.com"
        settings.KEYCLOAK_ADMIN_TOKEN = "fake-token"

        resp = customer_client.get(BASE_URL, _query())
        assert resp.status_code == 200
        assert resp.json()["data"] == {"available": False}

    def test_returns_not_available_when_keycloak_api_url_not_configured(
        self, customer_client, customer_with_profile, settings
    ):
        settings.KEYCLOAK_API_URL = ""
        _make_keycloak_service_access(customer_with_profile)

        resp = customer_client.get(BASE_URL, _query())
        assert resp.status_code == 200
        assert resp.json()["data"] == {"available": False}

    def test_returns_guide_with_verified_discovery(
        self, customer_client, customer_with_profile, settings
    ):
        settings.KEYCLOAK_API_URL = "https://keycloak.example.com"
        _make_keycloak_service_access(customer_with_profile, external_id="tenant-abc123")
        issuer = "https://keycloak.example.com/realms/tenant-abc123"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
            "token_endpoint": f"{issuer}/protocol/openid-connect/token",
            "userinfo_endpoint": f"{issuer}/protocol/openid-connect/userinfo",
            "jwks_uri": f"{issuer}/protocol/openid-connect/certs",
            "end_session_endpoint": f"{issuer}/protocol/openid-connect/logout",
        }
        with patch("apps.subscriptions.keycloak_guide.requests.get", return_value=mock_response):
            resp = customer_client.get(BASE_URL, _query(language="nextjs", app_name="Minha App"))

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["available"] is True
        assert data["verified"] is True
        assert data["issuer"] == issuer
        assert data["client_id_suggestion"] == "minha-app"
        # NextAuth tem caminho de callback fixo — não é o "/auth/callback" genérico.
        assert data["redirect_uri"] == "https://meusistema.com.br/api/auth/callback/keycloak"
        assert "next-auth" in data["package"]
        assert "__CLIENT_ID__" not in data["code_snippet"]
        assert "minha-app" in data["code_snippet"]
        assert issuer in data["code_snippet"]

    def test_returns_guide_with_fallback_endpoints_when_discovery_unreachable(
        self, customer_client, customer_with_profile, settings
    ):
        import requests

        settings.KEYCLOAK_API_URL = "https://keycloak.example.com"
        _make_keycloak_service_access(customer_with_profile, external_id="tenant-abc123")

        with patch(
            "apps.subscriptions.keycloak_guide.requests.get",
            side_effect=requests.ConnectionError("boom"),
        ):
            resp = customer_client.get(BASE_URL, _query(language="django"))

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["available"] is True
        assert data["verified"] is False
        issuer = "https://keycloak.example.com/realms/tenant-abc123"
        assert data["authorization_endpoint"] == f"{issuer}/protocol/openid-connect/auth"
        assert data["token_endpoint"] == f"{issuer}/protocol/openid-connect/token"

    def test_unknown_language_returns_400(self, customer_client, customer_with_profile, settings):
        settings.KEYCLOAK_API_URL = "https://keycloak.example.com"
        _make_keycloak_service_access(customer_with_profile)

        resp = customer_client.get(BASE_URL, _query(language="cobol"))
        assert resp.status_code == 400

    def test_invalid_base_url_returns_400(self, customer_client, customer_with_profile, settings):
        settings.KEYCLOAK_API_URL = "https://keycloak.example.com"
        _make_keycloak_service_access(customer_with_profile)

        resp = customer_client.get(BASE_URL, _query(base_url="not-a-url"))
        assert resp.status_code == 400

    def test_client_without_profile_gets_403(self, api_client, regular_user):
        from tests.conftest import _login

        _login(api_client, "user@papermoon.com", "user123")
        resp = api_client.get(BASE_URL, _query())
        assert resp.status_code in (403, 404)
