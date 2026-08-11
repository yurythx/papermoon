"""
Integration tests for the staff-facing Keycloak support tools
(apps/subscriptions/views_admin.py::AdminKeycloak*View):
- GET  /api/v1/admin/customers/<id>/keycloak-integration-guide/
- GET/POST /api/v1/admin/customers/<id>/keycloak-integrations/
- GET  /api/v1/admin/customers/<id>/keycloak-integrations/<id>/secret/
- POST /api/v1/admin/keycloak-tools/validate-issuer/

Staff opera em nome de um cliente escolhido (customer_id na URL) — mesma
lógica de apps.subscriptions.keycloak_guide reaproveitada da view do
cliente (ver test_keycloak_client_integrations.py), só muda quem autentica
e como o customer é resolvido.
"""

from unittest.mock import patch
import uuid

from django.core.cache import cache
import pytest
import requests

from apps.customers.models import Customer
from apps.products.models import Pricing, Product, ServiceComponent
from apps.provisioning.keycloak_config import update_keycloak_connection
from apps.subscriptions.models import (
    KeycloakClientIntegration,
    License,
    ServiceAccess,
    Subscription,
)

VALIDATE_ISSUER_URL = "/api/v1/admin/keycloak-tools/validate-issuer/"


def _guide_url(customer_id) -> str:
    return f"/api/v1/admin/customers/{customer_id}/keycloak-integration-guide/"


def _integrations_url(customer_id) -> str:
    return f"/api/v1/admin/customers/{customer_id}/keycloak-integrations/"


def _secret_url(customer_id, integration_id) -> str:
    return f"/api/v1/admin/customers/{customer_id}/keycloak-integrations/{integration_id}/secret/"


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def _configure_platform(admin_user, **overrides):
    defaults = {
        "enabled": True,
        "api_url": "https://keycloak.example.com",
        "admin_token": "admin-tok",
    }
    defaults.update(overrides)
    return update_keycloak_connection(user=admin_user, **defaults)


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


def _payload(**overrides):
    payload = {
        "language": "nextjs",
        "app_name": "Sistema do Cliente",
        "base_url": "https://sistema-cliente.com.br",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestAdminKeycloakIntegrationGuideView:
    def test_non_admin_returns_403(self, customer_client, customer_with_profile):
        resp = customer_client.get(
            _guide_url(customer_with_profile.id), _payload(base_url="https://x.com")
        )
        assert resp.status_code == 403

    def test_unauthenticated_returns_401(self, api_client, customer_with_profile):
        resp = api_client.get(_guide_url(customer_with_profile.id))
        assert resp.status_code == 401

    def test_unknown_customer_returns_404(self, admin_client, admin_user):
        _configure_platform(admin_user)
        resp = admin_client.get(
            _guide_url(uuid.uuid4()), {"language": "nextjs", "base_url": "https://x.com"}
        )
        assert resp.status_code == 404

    def test_generates_guide_for_chosen_customer(self, admin_client, customer, admin_user):
        _configure_platform(admin_user)
        _make_keycloak_service_access(customer, external_id="tenant-xyz")

        with patch(
            "apps.subscriptions.keycloak_guide.requests.get",
            side_effect=requests.ConnectionError("boom"),
        ):
            resp = admin_client.get(
                _guide_url(customer.id),
                {"language": "django", "app_name": "App", "base_url": "https://app.example.com"},
            )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["available"] is True
        assert "tenant-xyz" in data["issuer"]

    def test_unavailable_shows_exact_reason(self, admin_client, customer):
        # Sem configurar a KeycloakConnection central.
        resp = admin_client.get(
            _guide_url(customer.id), {"language": "nextjs", "base_url": "https://x.com"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["reason"] == "platform_not_configured"


@pytest.mark.django_db
class TestAdminKeycloakIntegrationListCreateView:
    def test_non_admin_returns_403(self, customer_client, customer_with_profile):
        resp = customer_client.get(_integrations_url(customer_with_profile.id))
        assert resp.status_code == 403

    def test_lists_integrations_for_chosen_customer(self, admin_client, customer, admin_user):
        _configure_platform(admin_user)
        service_access = _make_keycloak_service_access(customer)
        KeycloakClientIntegration.objects.create(
            service_access=service_access,
            client_id="app-do-cliente",
            kc_uuid="kc-uuid-1",
            realm="tenant-abc123",
            app_name="App do Cliente",
            base_url="https://app.com.br",
            redirect_uri="https://app.com.br/callback",
            language="django",
            public_client=False,
        )
        resp = admin_client.get(_integrations_url(customer.id))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["available"] is True
        assert len(data["integrations"]) == 1
        assert "client_secret" not in str(data["integrations"][0])

    def test_returns_exact_reason_when_platform_not_configured(self, admin_client, customer):
        resp = admin_client.post(_integrations_url(customer.id), _payload(), format="json")
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "platform_not_configured"

    def test_returns_exact_reason_when_no_service_access(self, admin_client, customer, admin_user):
        _configure_platform(admin_user)
        resp = admin_client.post(_integrations_url(customer.id), _payload(), format="json")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "no_service_access"

    def test_creates_real_client_for_chosen_customer(self, admin_client, customer, admin_user):
        _configure_platform(admin_user)
        _make_keycloak_service_access(customer, external_id="tenant-abc123")

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.create_oidc_client",
            return_value={
                "kc_uuid": "kc-uuid-99",
                "client_id": "sistema-do-cliente",
                "client_secret": "s3cr3t-real",
            },
        ) as mock_create:
            resp = admin_client.post(_integrations_url(customer.id), _payload(), format="json")

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["client_secret"] == "s3cr3t-real"
        mock_create.assert_called_once()

        integration = KeycloakClientIntegration.objects.get(client_id="sistema-do-cliente")
        assert integration.created_by_id is not None  # staff fica registrado como autor

        from apps.audit.models import AuditLog

        entry = AuditLog.objects.filter(action="keycloak_client_integration.created").first()
        assert entry is not None
        assert entry.changes["customer_id"] == str(customer.id)

    def test_unknown_customer_returns_404(self, admin_client, admin_user):
        _configure_platform(admin_user)
        resp = admin_client.post(_integrations_url(uuid.uuid4()), _payload(), format="json")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAdminKeycloakIntegrationSecretView:
    def test_returns_real_secret(self, admin_client, customer, admin_user):
        _configure_platform(admin_user)
        service_access = _make_keycloak_service_access(customer)
        integration = KeycloakClientIntegration.objects.create(
            service_access=service_access,
            client_id="app-do-cliente",
            kc_uuid="kc-uuid-1",
            realm="tenant-abc123",
            app_name="App do Cliente",
            base_url="https://app.com.br",
            redirect_uri="https://app.com.br/callback",
            language="django",
            public_client=False,
        )
        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.get_client_secret",
            return_value="fresh-secret",
        ):
            resp = admin_client.get(_secret_url(customer.id, integration.id))
        assert resp.status_code == 200
        assert resp.json()["data"]["client_secret"] == "fresh-secret"

    def test_wrong_customer_returns_404(self, admin_client, customer, admin_user):
        _configure_platform(admin_user)
        other_customer = Customer.objects.create(
            company_name="Outro Cliente", document="22.222.222/0001-22"
        )
        other_service_access = _make_keycloak_service_access(
            other_customer, external_id="tenant-other"
        )
        integration = KeycloakClientIntegration.objects.create(
            service_access=other_service_access,
            client_id="app-outro",
            kc_uuid="kc-uuid-2",
            realm="tenant-other",
            app_name="App Outro",
            base_url="https://outro.com.br",
            redirect_uri="https://outro.com.br/callback",
            language="js",
            public_client=True,
        )
        # Pedindo o secret pelo customer ERRADO (customer sem essa integração).
        resp = admin_client.get(_secret_url(customer.id, integration.id))
        assert resp.status_code == 404


@pytest.mark.django_db
class TestAdminKeycloakIssuerValidatorView:
    def test_non_admin_returns_403(self, customer_client):
        resp = customer_client.post(VALIDATE_ISSUER_URL, {"issuer": "https://x.com"}, format="json")
        assert resp.status_code == 403

    def test_invalid_issuer_returns_400(self, admin_client):
        resp = admin_client.post(VALIDATE_ISSUER_URL, {"issuer": "not-a-url"}, format="json")
        assert resp.status_code == 400

    def test_validates_arbitrary_issuer_without_any_customer(self, admin_client):
        issuer = "https://auth.cliente-externo.com.br/realms/algum-realm"
        mock_response = type(
            "Resp",
            (),
            {
                "raise_for_status": lambda self: None,
                "json": lambda self: {
                    "issuer": issuer,
                    "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
                    "token_endpoint": f"{issuer}/protocol/openid-connect/token",
                    "userinfo_endpoint": f"{issuer}/protocol/openid-connect/userinfo",
                    "jwks_uri": f"{issuer}/protocol/openid-connect/certs",
                    "end_session_endpoint": f"{issuer}/protocol/openid-connect/logout",
                },
            },
        )()
        with patch("apps.subscriptions.keycloak_guide.requests.get", return_value=mock_response):
            resp = admin_client.post(VALIDATE_ISSUER_URL, {"issuer": issuer}, format="json")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["verified"] is True
        assert data["issuer"] == issuer

    def test_falls_back_when_discovery_unreachable(self, admin_client):
        issuer = "https://auth.cliente-externo.com.br/realms/algum-realm"
        with patch(
            "apps.subscriptions.keycloak_guide.requests.get",
            side_effect=requests.ConnectionError("boom"),
        ):
            resp = admin_client.post(VALIDATE_ISSUER_URL, {"issuer": issuer}, format="json")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["verified"] is False
        assert data["authorization_endpoint"] == f"{issuer}/protocol/openid-connect/auth"
