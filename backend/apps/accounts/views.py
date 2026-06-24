from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.security import LoginAttemptGuard
from apps.accounts.serializers import RegisterSerializer
from shared.email import send_html_email
from shared.public_urls import build_frontend_url
from shared.schemas import (
    ChangePasswordRequestSerializer,
    LogoutRequestSerializer,
    MeResponseSerializer,
    MessageResponseSerializer,
    PasswordResetConfirmRequestSerializer,
)
from shared.schemas import (
    PasswordResetRequestSerializer as PasswordResetRequestBodySerializer,
)
from shared.throttling import (
    LoginRateThrottle,
    PasswordResetRateThrottle,
    RefreshRateThrottle,
    RegisterRateThrottle,
)

User = get_user_model()


@extend_schema(
    tags=["Auth"],
    summary="Obter tokens JWT",
    description=(
        "Retorna access (30 min, RS256) e refresh (7 dias, rotação automática) tokens. "
        "Bloqueio por 15 min após 5 tentativas falhas consecutivas do mesmo IP."
    ),
)
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request: Request, *args, **kwargs) -> Response:
        guard = LoginAttemptGuard(request)

        retry_after = guard.lockout_remaining()
        if retry_after:
            return Response(
                {
                    "code": "too_many_requests",
                    "message": (
                        f"Muitas tentativas de login. "
                        f"Tente novamente em {(retry_after // 60) + 1} minuto(s)."
                    ),
                    "details": [],
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(retry_after)},
            )

        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            guard.record_failure()
            raise

        guard.clear()
        return response


@extend_schema(
    tags=["Auth"],
    summary="Renovar access token",
    description="Troca o refresh token por um novo access token.",
)
class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [RefreshRateThrottle]


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Encerrar sessão",
        description="Adiciona o refresh token à blacklist, invalidando a sessão.",
        request=LogoutRequestSerializer,
        responses={200: MessageResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {
                    "code": "missing_token",
                    "message": "O refresh token é obrigatório.",
                    "details": [],
                },
                status=400,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {
                    "code": "invalid_token",
                    "message": "Token inválido ou já expirado.",
                    "details": [],
                },
                status=400,
            )
        return Response({"message": "Logout realizado com sucesso."})


@extend_schema(tags=["Auth"])
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Usuário autenticado",
        description="Retorna dados do usuário logado, seu customer (tenant) e role.",
        responses={200: MeResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        from apps.customers.models import CustomerProfile

        user = request.user
        profile = CustomerProfile.objects.select_related("customer").filter(user=user).first()

        data: dict = {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "is_staff": user.is_staff,
            },
            "customer": None,
            "role": None,
        }

        if profile:
            c = profile.customer
            data["customer"] = {
                "id": str(c.id),
                "company_name": c.company_name,
                "document": c.document,
                "status": c.status,
            }
            data["role"] = profile.role

        return Response(data)


@extend_schema(tags=["Auth"])
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    @extend_schema(
        summary="Solicitar redefinição de senha",
        description="Envia e-mail com link para redefinir senha. Sempre retorna 200 para não vazar existência de contas.",
        request=PasswordResetRequestBodySerializer,
        responses={200: MessageResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        email = request.data.get("email", "").strip().lower()
        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = build_frontend_url(
                "/reset-password",
                params={"uid": uid, "token": token},
            )
            send_html_email(
                subject="Redefinição de senha — PaperMoon",
                template_name="password_reset",
                context={"username": user.username, "reset_link": reset_link},
                recipient=user.email,
            )
        return Response(
            {"message": "Se o e-mail estiver cadastrado, você receberá um link em instantes."}
        )


@extend_schema(tags=["Auth"])
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    @extend_schema(
        summary="Confirmar redefinição de senha",
        description="Valida o token e define a nova senha.",
        request=PasswordResetConfirmRequestSerializer,
        responses={200: MessageResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        uid = request.data.get("uid", "")
        token = request.data.get("token", "")
        password = request.data.get("password", "")

        if not all([uid, token, password]):
            return Response(
                {
                    "code": "missing_fields",
                    "message": "uid, token e password são obrigatórios.",
                    "details": [],
                },
                status=400,
            )

        if len(password) < 8:
            return Response(
                {
                    "code": "validation_error",
                    "message": "A senha deve ter pelo menos 8 caracteres.",
                    "details": [],
                },
                status=400,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {"code": "invalid_token", "message": "Link inválido ou expirado.", "details": []},
                status=400,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"code": "invalid_token", "message": "Link inválido ou expirado.", "details": []},
                status=400,
            )

        user.set_password(password)
        user.save(update_fields=["password"])
        return Response({"message": "Senha redefinida com sucesso. Faça login com a nova senha."})


@extend_schema(tags=["Auth"])
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    @extend_schema(
        summary="Criar conta",
        description=(
            "Cria um novo usuário. Não cria o Customer — o admin provisiona após "
            "analisar o cadastro. O usuário é redirecionado para /onboarding até a "
            "equipe confirmar e vincular um Customer."
        ),
        request=RegisterSerializer,
        responses={201: None},
    )
    def post(self, request: Request) -> Response:
        from django.db import transaction

        from shared.models import OutboxEvent

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            user = User.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone=data.get("phone", ""),
            )
            OutboxEvent.objects.create(
                event_type="user.registered",
                payload={
                    "user_id": str(user.id),
                    "email": user.email,
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "company_name": data["company_name"],
                    "phone": data.get("phone", ""),
                },
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "company_name": data["company_name"],
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Admin — Users"])
class PendingRegistrationsView(APIView):
    """Lista usuários que se auto-cadastraram mas ainda não foram provisionados (sem CustomerProfile)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from apps.customers.models import CustomerProfile
        from shared.models import OutboxEvent

        if not request.user.is_staff:
            return Response(
                {"code": "permission_denied", "message": "Acesso negado.", "details": []},
                status=403,
            )

        provisioned_ids = CustomerProfile.objects.values_list("user_id", flat=True)
        pending_users = (
            User.objects.filter(is_staff=False, is_active=True)
            .exclude(id__in=provisioned_ids)
            .order_by("-date_joined")
        )

        outbox_by_user: dict = {}
        for event in OutboxEvent.objects.filter(event_type="user.registered").values("payload"):
            uid = event["payload"].get("user_id")
            if uid:
                outbox_by_user.setdefault(uid, event["payload"])

        results = []
        for u in pending_users:
            payload = outbox_by_user.get(str(u.id), {})
            results.append(
                {
                    "id": str(u.id),
                    "email": u.email,
                    "name": f"{u.first_name} {u.last_name}".strip() or payload.get("name", ""),
                    "company_name": payload.get("company_name", ""),
                    "phone": u.phone or payload.get("phone", ""),
                    "registered_at": u.date_joined.isoformat(),
                }
            )

        return Response(results)


@extend_schema(tags=["Admin — Users"])
class ProvisionUserView(APIView):
    """Cria Customer + CustomerProfile para um usuário pendente de provisionamento."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, user_id: str) -> Response:
        from django.db import transaction

        from apps.customers.models import Customer, CustomerProfile  # noqa: F401
        from apps.customers.repositories import DjangoCustomerRepository
        from apps.customers.services import CustomerService

        if not request.user.is_staff:
            return Response(
                {"code": "permission_denied", "message": "Acesso negado.", "details": []},
                status=403,
            )

        try:
            target_user = User.objects.get(pk=user_id, is_staff=False, is_active=True)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {"code": "not_found", "message": "Usuário não encontrado.", "details": []},
                status=404,
            )

        if CustomerProfile.objects.filter(user=target_user).exists():
            return Response(
                {
                    "code": "already_provisioned",
                    "message": "Usuário já possui um Customer vinculado.",
                    "details": [],
                },
                status=400,
            )

        company_name = (request.data.get("company_name") or "").strip()
        document = (request.data.get("document") or "").strip()
        if not company_name or not document:
            return Response(
                {
                    "code": "validation_error",
                    "message": "company_name e document são obrigatórios.",
                    "details": [],
                },
                status=400,
            )

        service = CustomerService(DjangoCustomerRepository())
        with transaction.atomic():
            customer = service.create_customer({"company_name": company_name, "document": document})
            CustomerProfile.objects.create(user=target_user, customer=customer, role="owner")

        from apps.customers.serializers import CustomerSerializer

        return Response(CustomerSerializer(customer).data, status=201)


@extend_schema(tags=["Auth"])
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Alterar senha",
        description="Troca a senha do usuário autenticado. Requer a senha atual.",
        request=ChangePasswordRequestSerializer,
        responses={200: MessageResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")

        if not current_password or not new_password:
            return Response(
                {
                    "code": "missing_fields",
                    "message": "current_password e new_password são obrigatórios.",
                    "details": [],
                },
                status=400,
            )

        if not request.user.check_password(current_password):
            return Response(
                {"code": "invalid_password", "message": "Senha atual incorreta.", "details": []},
                status=400,
            )

        if len(new_password) < 8:
            return Response(
                {
                    "code": "validation_error",
                    "message": "A nova senha deve ter pelo menos 8 caracteres.",
                    "details": [],
                },
                status=400,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        return Response({"message": "Senha alterada com sucesso."})
