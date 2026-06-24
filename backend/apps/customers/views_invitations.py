from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.commands import AcceptInvitationCommand
from apps.customers.serializers import AcceptInvitationSerializer
from shared.schemas import AcceptInviteResponseSerializer


@extend_schema(tags=["Client — Convites"])
class AcceptInvitationView(APIView):
    """
    Public endpoint — no JWT required.

    The invitee posts the token they received by e-mail plus a chosen password.
    On success a new CustomUser + CustomerProfile is created and the invitation
    is marked as accepted.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Aceitar convite (público)",
        description="Cria conta e vincula ao tenant a partir do token recebido por e-mail.",
        request=AcceptInvitationSerializer,
        responses={201: AcceptInviteResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = AcceptInvitationCommand(
            token=serializer.validated_data["token"],
            password=serializer.validated_data["password"],
        ).execute()
        return Response(
            {
                "message": "Convite aceito com sucesso.",
                "customer_id": str(profile.customer_id),
                "role": profile.role,
            },
            status=201,
        )
