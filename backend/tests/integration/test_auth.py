import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    from apps.accounts.models import CustomUser

    return CustomUser.objects.create_user(
        username="testuser",
        email="test@papermoon.com",
        password="testpass123",
    )


@pytest.mark.django_db
class TestLoginEndpoint:
    def test_login_returns_tokens(self, client, user):
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "test@papermoon.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access" in data["data"]
        assert "refresh" in data["data"]

    def test_login_wrong_password_returns_401(self, client, user):
        response = client.post(
            "/api/v1/auth/login/",
            {"email": "test@papermoon.com", "password": "wrong"},
            format="json",
        )
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "authentication_failed"

    def test_login_missing_fields_returns_400(self, client):
        response = client.post("/api/v1/auth/login/", {}, format="json")
        assert response.status_code == 400

    def test_logout_blacklists_token(self, client, user):
        login = client.post(
            "/api/v1/auth/login/",
            {"email": "test@papermoon.com", "password": "testpass123"},
            format="json",
        ).json()
        refresh = login["data"]["refresh"]
        access = login["data"]["access"]

        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.post("/api/v1/auth/logout/", {"refresh": refresh}, format="json")
        assert response.status_code == 200

        # Usar o refresh expirado deve falhar
        response2 = client.post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json")
        assert response2.status_code == 401


@pytest.mark.django_db
class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["db"] == "ok"


@pytest.mark.django_db
class TestMeEndpoint:
    def test_me_returns_user_and_customer(self, client, db):
        from apps.accounts.models import CustomUser
        from apps.customers.models import Customer, CustomerProfile

        user = CustomUser.objects.create_user(
            username="meuser", email="me@papermoon.com", password="pass123"
        )
        customer = Customer.objects.create(company_name="Me Corp", document="11.111.111/0001-11")
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")

        login = client.post(
            "/api/v1/auth/login/",
            {"email": "me@papermoon.com", "password": "pass123"},
            format="json",
        ).json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['data']['access']}")

        resp = client.get("/api/v1/auth/me/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["user"]["email"] == "me@papermoon.com"
        assert data["customer"]["company_name"] == "Me Corp"
        assert data["role"] == "owner"

    def test_me_includes_first_and_last_name(self, client, db):
        # Regressão: o dict manual de MeView já esqueceu first_name/last_name
        # uma vez, fazendo o nome do usuário sumir do topbar e reaparecer só o
        # e-mail/username em qualquer tela que dependesse de /auth/me.
        from apps.accounts.models import CustomUser

        CustomUser.objects.create_user(
            username="named",
            email="named@papermoon.com",
            password="pass123",
            first_name="Yuri",
            last_name="Menezes",
        )

        login = client.post(
            "/api/v1/auth/login/",
            {"email": "named@papermoon.com", "password": "pass123"},
            format="json",
        ).json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['data']['access']}")

        resp = client.get("/api/v1/auth/me/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["user"]["first_name"] == "Yuri"
        assert data["user"]["last_name"] == "Menezes"

    def test_me_admin_returns_no_customer(self, client, db):
        from apps.accounts.models import CustomUser

        CustomUser.objects.create_superuser(
            username="admin_me", email="admin_me@papermoon.com", password="admin123"
        )

        login = client.post(
            "/api/v1/auth/login/",
            {"email": "admin_me@papermoon.com", "password": "admin123"},
            format="json",
        ).json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['data']['access']}")

        resp = client.get("/api/v1/auth/me/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["user"]["is_staff"] is True
        assert data["customer"] is None
        assert data["role"] is None

    def test_me_unauthenticated_returns_401(self, client):
        resp = client.get("/api/v1/auth/me/")
        assert resp.status_code == 401

    def test_me_includes_feature_flags_enabled_for_the_customer(self, client, db):
        from apps.accounts.models import CustomUser
        from apps.customers.models import Customer, CustomerProfile
        from apps.flags.models import FeatureFlag

        user = CustomUser.objects.create_user(
            username="flaguser", email="flaguser@papermoon.com", password="pass123"
        )
        customer = Customer.objects.create(company_name="Flag Corp", document="22.222.222/0001-22")
        CustomerProfile.objects.create(user=user, customer=customer, role="owner")
        FeatureFlag.objects.create(key="site_wide", name="Site wide", enabled_globally=True)
        beta = FeatureFlag.objects.create(key="beta_widget", name="Beta widget")
        beta.enabled_customers.add(customer)
        FeatureFlag.objects.create(key="off_for_everyone", name="Off")

        login = client.post(
            "/api/v1/auth/login/",
            {"email": "flaguser@papermoon.com", "password": "pass123"},
            format="json",
        ).json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['data']['access']}")

        resp = client.get("/api/v1/auth/me/")
        assert resp.status_code == 200
        assert sorted(resp.json()["data"]["feature_flags"]) == ["beta_widget", "site_wide"]


@pytest.mark.django_db
class TestChangePasswordEndpoint:
    URL = "/api/v1/auth/change-password/"

    def _auth_client(self, user):
        from rest_framework.test import APIClient

        login = (
            APIClient()
            .post(
                "/api/v1/auth/login/",
                {"email": user.email, "password": "testpass123"},
                format="json",
            )
            .json()
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {login['data']['access']}")
        return c

    def test_change_password_success(self, user):
        c = self._auth_client(user)
        resp = c.post(
            self.URL,
            {"current_password": "testpass123", "new_password": "newsecure99"},
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.check_password("newsecure99")

    def test_wrong_current_password_returns_400(self, user):
        c = self._auth_client(user)
        resp = c.post(
            self.URL, {"current_password": "wrong", "new_password": "newsecure99"}, format="json"
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_password"

    def test_new_password_too_short_returns_400(self, user):
        c = self._auth_client(user)
        resp = c.post(
            self.URL, {"current_password": "testpass123", "new_password": "short"}, format="json"
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "validation_error"

    def test_missing_fields_returns_400(self, user):
        c = self._auth_client(user)
        resp = c.post(self.URL, {}, format="json")
        assert resp.status_code == 400

    def test_unauthenticated_returns_401(self):
        from rest_framework.test import APIClient

        resp = APIClient().post(
            self.URL, {"current_password": "x", "new_password": "y"}, format="json"
        )
        assert resp.status_code == 401


@pytest.mark.django_db
class TestPasswordResetEndpoints:
    REQUEST_URL = "/api/v1/auth/password-reset/"
    CONFIRM_URL = "/api/v1/auth/password-reset/confirm/"

    def test_request_always_returns_200_even_for_unknown_email(self):
        from rest_framework.test import APIClient

        resp = APIClient().post(self.REQUEST_URL, {"email": "nobody@nowhere.com"}, format="json")
        assert resp.status_code == 200

    def test_request_sends_email_for_known_user(self, user):
        from unittest.mock import patch

        from rest_framework.test import APIClient

        with patch("apps.accounts.views.send_html_email") as mock_mail:
            APIClient().post(self.REQUEST_URL, {"email": user.email}, format="json")
            assert mock_mail.called
            kw = mock_mail.call_args.kwargs
            assert kw["recipient"] == user.email

    def test_confirm_with_valid_token_changes_password(self, user):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from rest_framework.test import APIClient

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        resp = APIClient().post(
            self.CONFIRM_URL,
            {"uid": uid, "token": token, "password": "newpassword99"},
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.check_password("newpassword99")

    def test_confirm_with_invalid_token_returns_400(self, user):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from rest_framework.test import APIClient

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        resp = APIClient().post(
            self.CONFIRM_URL,
            {"uid": uid, "token": "invalid-token", "password": "newpassword99"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_token"

    def test_confirm_password_too_short_returns_400(self, user):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from rest_framework.test import APIClient

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        resp = APIClient().post(
            self.CONFIRM_URL,
            {"uid": uid, "token": token, "password": "short"},
            format="json",
        )
        assert resp.status_code == 400

    def test_confirm_missing_fields_returns_400(self):
        from rest_framework.test import APIClient

        resp = APIClient().post(self.CONFIRM_URL, {}, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestSSOEndpoints:
    LOGIN_URL = "/api/v1/auth/sso/login/"
    CALLBACK_URL = "/api/v1/auth/sso/callback/"

    def test_login_not_configured_returns_503(self, client):
        from unittest.mock import patch

        from apps.accounts.oidc import SSONotConfiguredError

        with patch(
            "apps.accounts.views.build_authorize_url", side_effect=SSONotConfiguredError("x")
        ):
            resp = client.get(self.LOGIN_URL)
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "sso_not_configured"

    def test_login_returns_authorize_url(self, client):
        from unittest.mock import patch

        with patch(
            "apps.accounts.views.build_authorize_url",
            return_value="https://keycloak.example.com/authorize?state=abc",
        ):
            resp = client.get(self.LOGIN_URL)
        assert resp.status_code == 200
        assert resp.json()["data"]["authorize_url"].startswith("https://keycloak.example.com")

    def test_callback_missing_fields_returns_400(self, client):
        resp = client.post(self.CALLBACK_URL, {}, format="json")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "missing_fields"

    def test_callback_invalid_state_returns_400(self, client):
        from unittest.mock import patch

        from apps.accounts.oidc import SSOStateInvalidError

        with patch("apps.accounts.views.exchange_code", side_effect=SSOStateInvalidError("x")):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "bad"}, format="json")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "invalid_state"

    def test_callback_exchange_failure_returns_400(self, client):
        from unittest.mock import patch

        from apps.accounts.oidc import SSOExchangeFailedError

        with patch("apps.accounts.views.exchange_code", side_effect=SSOExchangeFailedError("x")):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "s"}, format="json")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "sso_exchange_failed"

    def test_callback_non_staff_account_returns_403(self, client, user):
        from unittest.mock import patch

        from apps.accounts.oidc import SSOClaims

        # `user` fixture is not is_staff — same account exists, but has no backoffice access.
        with patch(
            "apps.accounts.views.exchange_code",
            return_value=SSOClaims(email=user.email, subject="kc-sub-1"),
        ):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "s"}, format="json")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "sso_account_not_staff"

    def test_callback_unknown_email_returns_403(self, client):
        from unittest.mock import patch

        from apps.accounts.oidc import SSOClaims

        with patch(
            "apps.accounts.views.exchange_code",
            return_value=SSOClaims(email="ghost@papermoon.com", subject="kc-sub-2"),
        ):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "s"}, format="json")
        assert resp.status_code == 403

    def test_callback_staff_account_issues_tokens(self, client, db):
        from unittest.mock import patch

        from apps.accounts.models import CustomUser
        from apps.accounts.oidc import SSOClaims

        staff = CustomUser.objects.create_user(
            username="staffsso",
            email="staff@papermoon.com",
            password="unused-password",
            is_staff=True,
        )

        with patch(
            "apps.accounts.views.exchange_code",
            return_value=SSOClaims(email=staff.email, subject="kc-sub-3"),
        ):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "s"}, format="json")
        assert resp.status_code == 200

    def test_callback_jit_provisioning_populates_first_and_last_name(self, client, db):
        # Regressão: contas criadas na hora (JIT) por um primeiro login SSO
        # ficavam com first_name/last_name vazios porque SSOClaims nem
        # capturava given_name/family_name — o autor de posts do blog (e o
        # topbar) mostravam e-mail/username em vez do nome de verdade.
        from unittest.mock import patch

        from apps.accounts.models import CustomUser, SSOConfiguration
        from apps.accounts.oidc import SSOClaims
        from apps.accounts.sso_config import invalidate_sso_config_cache
        from shared.crypto import encrypt_secret

        SSOConfiguration.objects.update_or_create(
            pk=1,
            defaults={
                "enabled": True,
                "issuer": "https://keycloak.example.com/realms/papermoon",
                "client_id": "papermoon-staff",
                "client_secret_encrypted": encrypt_secret("shh"),
                "staff_group": "papermoon-staff",
            },
        )
        invalidate_sso_config_cache()

        with patch(
            "apps.accounts.views.exchange_code",
            return_value=SSOClaims(
                email="new.staff@rondonopolis.mt.gov.br",
                subject="kc-sub-new",
                groups=("papermoon-staff",),
                first_name="Yuri",
                last_name="Menezes",
            ),
        ):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "s"}, format="json")

        assert resp.status_code == 200
        created = CustomUser.objects.get(email="new.staff@rondonopolis.mt.gov.br")
        assert created.first_name == "Yuri"
        assert created.last_name == "Menezes"
        assert created.is_staff is True

    def test_callback_syncs_name_on_login_for_existing_account(self, client, db):
        from unittest.mock import patch

        from apps.accounts.models import CustomUser
        from apps.accounts.oidc import SSOClaims

        staff = CustomUser.objects.create_user(
            username="oldstaffsso",
            email="oldstaff@papermoon.com",
            password="unused-password",
            is_staff=True,
            # Simula uma conta JIT criada antes desse sync existir.
            first_name="",
            last_name="",
        )

        with patch(
            "apps.accounts.views.exchange_code",
            return_value=SSOClaims(
                email=staff.email, subject="kc-sub-4", first_name="Yuri", last_name="Menezes"
            ),
        ):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "s"}, format="json")

        assert resp.status_code == 200
        staff.refresh_from_db()
        assert staff.first_name == "Yuri"
        assert staff.last_name == "Menezes"

    def test_callback_does_not_erase_existing_name_when_claims_have_no_name(self, client, db):
        # Um id_token sem given_name/family_name/name (realm com mapper
        # incompleto) nunca deve apagar um nome já sincronizado antes.
        from unittest.mock import patch

        from apps.accounts.models import CustomUser
        from apps.accounts.oidc import SSOClaims

        staff = CustomUser.objects.create_user(
            username="namedstaffsso",
            email="namedstaff@papermoon.com",
            password="unused-password",
            is_staff=True,
            first_name="Yuri",
            last_name="Menezes",
        )

        with patch(
            "apps.accounts.views.exchange_code",
            return_value=SSOClaims(email=staff.email, subject="kc-sub-5"),
        ):
            resp = client.post(self.CALLBACK_URL, {"code": "abc", "state": "s"}, format="json")

        assert resp.status_code == 200
        staff.refresh_from_db()
        assert staff.first_name == "Yuri"
        assert staff.last_name == "Menezes"
        data = resp.json()["data"]
        assert "access" in data
        assert "refresh" in data


@pytest.mark.django_db
class TestRegisterEndpoint:
    URL = "/api/v1/auth/register/"

    def test_register_creates_user_and_returns_tokens(self, client):
        resp = client.post(
            self.URL,
            {
                "first_name": "João",
                "last_name": "Silva",
                "company_name": "Acme Ltda",
                "email": "joao@acme.com",
                "password": "secure123",
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "access" in data
        assert "refresh" in data
        assert data["company_name"] == "Acme Ltda"

    def test_register_creates_outbox_event(self, client):
        from shared.models import OutboxEvent

        client.post(
            self.URL,
            {
                "first_name": "Maria",
                "last_name": "Santos",
                "company_name": "Tech Co",
                "email": "maria@techco.com",
                "password": "secure123",
            },
            format="json",
        )
        event = OutboxEvent.objects.filter(event_type="user.registered").first()
        assert event is not None
        assert event.payload["company_name"] == "Tech Co"
        assert event.payload["email"] == "maria@techco.com"

    def test_register_stores_company_name_in_payload(self, client):
        from shared.models import OutboxEvent

        client.post(
            self.URL,
            {
                "first_name": "Carlos",
                "last_name": "Lima",
                "company_name": "Lima Tecnologia",
                "email": "carlos@lima.com",
                "password": "secure123",
            },
            format="json",
        )
        event = OutboxEvent.objects.get(event_type="user.registered")
        assert event.payload["name"] == "Carlos Lima"
        assert event.payload["company_name"] == "Lima Tecnologia"

    def test_register_with_optional_phone(self, client):
        from apps.accounts.models import CustomUser

        resp = client.post(
            self.URL,
            {
                "first_name": "Ana",
                "last_name": "Lima",
                "company_name": "Lima Tech",
                "email": "ana@lima.com",
                "password": "secure123",
                "phone": "(11) 99999-9999",
            },
            format="json",
        )
        assert resp.status_code == 201
        user = CustomUser.objects.get(email="ana@lima.com")
        assert user.phone == "(11) 99999-9999"

    def test_register_duplicate_email_returns_400(self, client, user):
        resp = client.post(
            self.URL,
            {
                "first_name": "Dup",
                "last_name": "User",
                "company_name": "Dup Corp",
                "email": user.email,
                "password": "secure123",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "validation_error"

    def test_register_numeric_password_returns_400(self, client):
        resp = client.post(
            self.URL,
            {
                "first_name": "Test",
                "last_name": "User",
                "company_name": "Test Co",
                "email": "numeric@test.com",
                "password": "12345678",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_register_short_password_returns_400(self, client):
        resp = client.post(
            self.URL,
            {
                "first_name": "Test",
                "last_name": "User",
                "company_name": "Test Co",
                "email": "short@test.com",
                "password": "abc",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_register_missing_required_fields_returns_400(self, client):
        resp = client.post(self.URL, {"email": "missing@test.com"}, format="json")
        assert resp.status_code == 400

    def test_register_lowercases_email(self, client):
        from apps.accounts.models import CustomUser

        client.post(
            self.URL,
            {
                "first_name": "Test",
                "last_name": "Case",
                "company_name": "Test Corp",
                "email": "Upper@CASE.COM",
                "password": "secure123",
            },
            format="json",
        )
        assert CustomUser.objects.filter(email="upper@case.com").exists()

    def test_register_no_auth_required(self, client):
        """Must be accessible without a token — it's AllowAny."""
        resp = client.post(
            self.URL,
            {
                "first_name": "Anon",
                "last_name": "User",
                "company_name": "Anon Corp",
                "email": "anon@corp.com",
                "password": "secure123",
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_register_throttle_class_wired(self):
        from apps.accounts.views import RegisterView
        from shared.throttling import RegisterRateThrottle

        assert RegisterRateThrottle in RegisterView.throttle_classes


class TestLoginThrottleWiring:
    """Verifica a ligação entre views e throttle classes — sem testar o rate-limiter em si."""

    def test_login_view_has_login_rate_throttle(self):
        from apps.accounts.views import LoginView
        from shared.throttling import LoginRateThrottle

        assert LoginRateThrottle in LoginView.throttle_classes

    def test_refresh_view_has_refresh_rate_throttle(self):
        from apps.accounts.views import RefreshTokenView
        from shared.throttling import RefreshRateThrottle

        assert RefreshRateThrottle in RefreshTokenView.throttle_classes

    def test_login_throttle_scope(self):
        from shared.throttling import LoginRateThrottle

        assert LoginRateThrottle.scope == "login"

    def test_refresh_throttle_scope(self):
        from shared.throttling import RefreshRateThrottle

        assert RefreshRateThrottle.scope == "token_refresh"

    def test_login_rate_configured_in_settings(self, settings):
        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        assert "login" in rates
        # Deve ser stricter que o rate geral de anon
        assert rates["login"].endswith("/minute")

    def test_refresh_rate_configured_in_settings(self, settings):
        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        assert "token_refresh" in rates
