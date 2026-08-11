"""
Integration tests for apps/subscriptions/views_client.py::
ClientKeycloakIntegrationListCreateView e ClientKeycloakIntegrationSecretView —
a criação REAL de client OIDC no Keycloak do cliente (não o guia read-only,
que é testado em test_keycloak_integration_guide_view.py).

HTTP real ao Keycloak nunca acontece — apps.provisioning.keycloak.
KeycloakProvisioner.create_oidc_client/get_client_secret são mockados a nível
de classe, então funciona independente de qual módulo instancia o provisioner.
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

LIST_URL = "/api/v1/client/subscriptions/keycloak-integrations/"


def _secret_url(pk) -> str:
    return f"/api/v1/client/subscriptions/keycloak-integrations/{pk}/secret/"


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


def _create_payload(**overrides):
    payload = {
        "language": "nextjs",
        "app_name": "Minha App",
        "base_url": "https://meusistema.com.br",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestListView:
    def test_unavailable_when_platform_not_configured(self, customer_client, customer_with_profile):
        resp = customer_client.get(LIST_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["available"] is False
        assert data["reason"] == "platform_not_configured"
        assert data["integrations"] == []

    def test_unavailable_when_no_service_access(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        resp = customer_client.get(LIST_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["available"] is False
        assert data["reason"] == "no_service_access"

    def test_available_and_lists_existing_integrations_without_secret(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        service_access = _make_keycloak_service_access(customer_with_profile)
        KeycloakClientIntegration.objects.create(
            service_access=service_access,
            client_id="ja-existe",
            kc_uuid="kc-uuid-1",
            realm="tenant-abc123",
            app_name="Já Existe",
            base_url="https://ja-existe.com.br",
            redirect_uri="https://ja-existe.com.br/callback",
            language="js",
            public_client=True,
        )

        resp = customer_client.get(LIST_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["available"] is True
        assert data["reason"] is None
        assert len(data["integrations"]) == 1
        assert data["integrations"][0]["client_id"] == "ja-existe"
        assert "client_secret" not in str(data["integrations"][0])

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(LIST_URL)
        assert resp.status_code == 401


@pytest.mark.django_db
class TestCreateView:
    def test_returns_409_when_platform_not_configured(self, customer_client, customer_with_profile):
        resp = customer_client.post(LIST_URL, _create_payload(), format="json")
        assert resp.status_code == 409

    def test_returns_403_when_no_service_access(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        resp = customer_client.post(LIST_URL, _create_payload(), format="json")
        assert resp.status_code == 403

    def test_unknown_language_returns_400(self, customer_client, customer_with_profile, admin_user):
        _configure_platform(admin_user)
        _make_keycloak_service_access(customer_with_profile)
        resp = customer_client.post(LIST_URL, _create_payload(language="cobol"), format="json")
        assert resp.status_code == 400

    def test_invalid_base_url_returns_400(self, customer_client, customer_with_profile, admin_user):
        _configure_platform(admin_user)
        _make_keycloak_service_access(customer_with_profile)
        resp = customer_client.post(LIST_URL, _create_payload(base_url="not-a-url"), format="json")
        assert resp.status_code == 400

    def test_creates_confidential_client_and_returns_real_secret(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        _make_keycloak_service_access(customer_with_profile, external_id="tenant-abc123")

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.create_oidc_client",
            return_value={
                "kc_uuid": "kc-uuid-99",
                "client_id": "minha-app",
                "client_secret": "s3cr3t-real",
            },
        ) as mock_create:
            resp = customer_client.post(LIST_URL, _create_payload(language="nextjs"), format="json")

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["client_id"] == "minha-app"
        assert data["client_secret"] == "s3cr3t-real"
        assert data["public_client"] is False
        assert "s3cr3t-real" in data["code_snippet"]
        assert "__CLIENT_SECRET__" not in data["code_snippet"]

        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs["realm"] == "tenant-abc123"
        assert mock_create.call_args.kwargs["public_client"] is False

        integration = KeycloakClientIntegration.objects.get(client_id="minha-app")
        assert integration.kc_uuid == "kc-uuid-99"
        assert integration.public_client is False

        from apps.audit.models import AuditLog

        entry = AuditLog.objects.filter(action="keycloak_client_integration.created").first()
        assert entry is not None
        assert "s3cr3t-real" not in str(entry.changes)

    def test_creates_public_client_without_secret(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        _make_keycloak_service_access(customer_with_profile)

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.create_oidc_client",
            return_value={"kc_uuid": "kc-uuid-1", "client_id": "minha-app", "client_secret": None},
        ) as mock_create:
            resp = customer_client.post(LIST_URL, _create_payload(language="js"), format="json")

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["client_secret"] is None
        assert data["public_client"] is True
        assert mock_create.call_args.kwargs["public_client"] is True

    def test_duplicate_client_id_in_db_returns_409_without_calling_keycloak(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        service_access = _make_keycloak_service_access(customer_with_profile)
        KeycloakClientIntegration.objects.create(
            service_access=service_access,
            client_id="minha-app",
            kc_uuid="kc-uuid-existing",
            realm="tenant-abc123",
            app_name="Minha App",
            base_url="https://meusistema.com.br",
            redirect_uri="https://meusistema.com.br/callback",
            language="nextjs",
            public_client=False,
        )

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.create_oidc_client"
        ) as mock_create:
            resp = customer_client.post(
                LIST_URL, _create_payload(app_name="Minha App"), format="json"
            )

        assert resp.status_code == 409
        mock_create.assert_not_called()

    def test_duplicate_client_id_at_keycloak_returns_409(
        self, customer_client, customer_with_profile, admin_user
    ):
        from apps.provisioning.keycloak import KeycloakClientAlreadyExistsError

        _configure_platform(admin_user)
        _make_keycloak_service_access(customer_with_profile)

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.create_oidc_client",
            side_effect=KeycloakClientAlreadyExistsError("minha-app"),
        ):
            resp = customer_client.post(LIST_URL, _create_payload(), format="json")
        assert resp.status_code == 409

    def test_keycloak_unreachable_returns_502(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        _make_keycloak_service_access(customer_with_profile)

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.create_oidc_client",
            side_effect=requests.ConnectionError("boom"),
        ):
            resp = customer_client.post(LIST_URL, _create_payload(), format="json")
        assert resp.status_code == 502

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.post(LIST_URL, _create_payload(), format="json")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestSecretView:
    def _create_integration(self, service_access, *, public_client=False, client_id="minha-app"):
        return KeycloakClientIntegration.objects.create(
            service_access=service_access,
            client_id=client_id,
            kc_uuid="kc-uuid-1",
            realm="tenant-abc123",
            app_name="Minha App",
            base_url="https://meusistema.com.br",
            redirect_uri="https://meusistema.com.br/callback",
            language="nextjs",
            public_client=public_client,
        )

    def test_returns_real_secret(self, customer_client, customer_with_profile, admin_user):
        _configure_platform(admin_user)
        service_access = _make_keycloak_service_access(customer_with_profile)
        integration = self._create_integration(service_access)

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.get_client_secret",
            return_value="fresh-secret",
        ) as mock_get:
            resp = customer_client.get(_secret_url(integration.id))

        assert resp.status_code == 200
        assert resp.json()["data"]["client_secret"] == "fresh-secret"
        mock_get.assert_called_once_with(realm="tenant-abc123", kc_uuid="kc-uuid-1")

    def test_public_client_returns_400(self, customer_client, customer_with_profile, admin_user):
        _configure_platform(admin_user)
        service_access = _make_keycloak_service_access(customer_with_profile)
        integration = self._create_integration(service_access, public_client=True)

        resp = customer_client.get(_secret_url(integration.id))
        assert resp.status_code == 400

    def test_other_customers_integration_returns_404(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        other_customer = Customer.objects.create(
            company_name="Outra Empresa", document="11.111.111/0001-11"
        )
        other_service_access = _make_keycloak_service_access(
            other_customer, external_id="tenant-other"
        )
        integration = self._create_integration(other_service_access)

        resp = customer_client.get(_secret_url(integration.id))
        assert resp.status_code == 404

    def test_keycloak_unreachable_returns_502(
        self, customer_client, customer_with_profile, admin_user
    ):
        _configure_platform(admin_user)
        service_access = _make_keycloak_service_access(customer_with_profile)
        integration = self._create_integration(service_access)

        with patch(
            "apps.provisioning.keycloak.KeycloakProvisioner.get_client_secret",
            side_effect=requests.ConnectionError("boom"),
        ):
            resp = customer_client.get(_secret_url(integration.id))
        assert resp.status_code == 502

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(_secret_url(uuid.uuid4()))
        assert resp.status_code == 401
