from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.models import CustomerProfile
from apps.notifications.commands import MarkAllNotificationsReadCommand, MarkNotificationReadCommand
from apps.notifications.models import Notification
from apps.notifications.queries import list_in_app_notifications
from shared.schemas import MessageResponseSerializer, NotificationItemSerializer


def _serialize_notification(n: "Notification") -> dict:
    return {
        "id": str(n.id),
        "event_type": n.event_type,
        "subject": n.subject,
        "body": n.body,
        "is_read": n.status == Notification.Status.SENT,
        "created_at": n.created_at.isoformat(),
        "read_at": n.sent_at.isoformat() if n.sent_at else None,
    }


def _resolve_customer(user):
    profile = CustomerProfile.objects.select_related("customer").filter(user=user).first()
    if not profile:
        raise NotFound("Perfil de cliente não encontrado.")
    return profile.customer


@extend_schema(tags=["Client — Notificações"])
class InAppNotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar notificações in-app",
        description=(
            "Retorna notificações do customer ordenadas por mais recente. "
            "Sem ?page retorna as últimas 20 (para o sino). "
            "Com ?page=N retorna 20 por página para a listagem completa."
        ),
        responses={200: NotificationItemSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        from django.core.paginator import Paginator

        customer = _resolve_customer(request.user)
        base_qs = list_in_app_notifications(str(customer.id))

        unread_count = base_qs.filter(status=Notification.Status.PENDING).count()

        page_param = request.query_params.get("page")
        if page_param:
            paginator = Paginator(base_qs, 20)
            try:
                page_num = int(page_param)
            except ValueError:
                page_num = 1
            page_obj = paginator.get_page(page_num)
            items = list(page_obj)
            results = [_serialize_notification(n) for n in items]
            return Response(
                {
                    "count": paginator.count,
                    "unread_count": unread_count,
                    "num_pages": paginator.num_pages,
                    "page": page_obj.number,
                    "results": results,
                }
            )

        # No page param — return latest 20 for the notification bell
        items = list(base_qs[:20])
        results = [_serialize_notification(n) for n in items]
        return Response({"count": len(results), "unread_count": unread_count, "results": results})


@extend_schema(tags=["Client — Notificações"])
class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Marcar notificação como lida",
        request=None,
        responses={200: MessageResponseSerializer},
    )
    def post(self, request: Request, pk: str) -> Response:
        customer = _resolve_customer(request.user)
        try:
            MarkNotificationReadCommand().execute(pk, str(customer.id))
        except NotFound:
            return Response(
                {"code": "not_found", "message": "Notificação não encontrada.", "details": []},
                status=404,
            )
        return Response({"message": "Notificação marcada como lida."})


@extend_schema(tags=["Client — Notificações"])
class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Marcar todas as notificações como lidas",
        request=None,
        responses={200: MessageResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        customer = _resolve_customer(request.user)
        updated = MarkAllNotificationsReadCommand().execute(str(customer.id))
        return Response({"message": f"{updated} notificações marcadas como lidas."})
