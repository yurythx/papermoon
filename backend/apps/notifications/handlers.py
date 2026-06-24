"""Notification handlers for billing and customer lifecycle OutboxEvents."""

import logging

from apps.notifications.registry import register
from shared.public_urls import build_frontend_url

# Import provisioning handlers so they register their subscriptions at Django startup.
import apps.provisioning.handlers  # noqa: F401

logger = logging.getLogger(__name__)


@register("payment.processed")
def email_payment_confirmed(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_payment_confirmed_email

    send_payment_confirmed_email.delay(payload["invoice_id"], event_id)


@register("payment.processed")
def renew_subscription_on_payment(payload: dict, event_id: str) -> None:
    """If the invoice is linked to a subscription, renew it on payment confirmation."""
    subscription_id = payload.get("subscription_id")
    if not subscription_id:
        return

    from apps.subscriptions.commands import RenewSubscriptionCommand
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    if sub.status in {
        Subscription.Status.ACTIVE,
        Subscription.Status.GRACE_PERIOD,
        Subscription.Status.EXPIRED,
        Subscription.Status.SUSPENDED,
    }:
        try:
            RenewSubscriptionCommand().execute(subscription_id)
        except Exception as exc:
            logger.error("renew_subscription_on_payment sub_id=%s error=%s", subscription_id, exc)


@register("payment.due_soon")
def email_payment_due_soon(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_payment_due_soon_email

    send_payment_due_soon_email.delay(payload["invoice_id"], event_id)


@register("payment.failed")
def email_payment_overdue(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_payment_overdue_email

    send_payment_overdue_email.delay(payload["invoice_id"], event_id)


@register("customer.suspended")
def email_customer_suspended(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_customer_suspended_email

    send_customer_suspended_email.delay(payload["customer_id"], event_id)


@register("customer.reactivated")
def email_customer_reactivated(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_customer_reactivated_email

    send_customer_reactivated_email.delay(payload["customer_id"], event_id)


@register("customer.cancelled")
def email_customer_cancelled(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_customer_cancelled_email

    send_customer_cancelled_email.delay(payload["customer_id"], event_id)


@register("charge.registered")
def log_charge_registered(payload: dict, event_id: str) -> None:
    logger.info(
        "charge.registered event_id=%s invoice_id=%s asaas_id=%s",
        event_id,
        payload.get("invoice_id"),
        payload.get("asaas_id"),
    )


@register("charge.registered")
def email_invoice_ready(payload: dict, event_id: str) -> None:
    """Sends the client an email with the Asaas payment link as soon as the charge is created."""
    from apps.notifications.tasks import send_invoice_ready_email

    send_invoice_ready_email.delay(payload["invoice_id"], event_id)


@register("customer.created")
def provision_asaas_customer(payload: dict, event_id: str) -> None:
    """
    Provisions the new customer in Asaas so future invoices can be created.
    Runs asynchronously via Outbox — the HTTP call to Asaas is outside any DB transaction.
    """
    from apps.billing.customer_commands import ProvisionAsaasCustomerCommand

    try:
        ProvisionAsaasCustomerCommand().execute(payload["customer_id"])
    except Exception as exc:
        logger.error(
            "provision_asaas_customer failed customer_id=%s error=%s",
            payload.get("customer_id"),
            exc,
        )
        raise  # re-raise so OutboxEvent retry logic kicks in


@register("customer.created")
def email_customer_created(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_customer_created_email

    send_customer_created_email.delay(payload["customer_id"], event_id)


@register("subscription.created")
def email_subscription_created(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_created_email

    send_subscription_created_email.delay(payload["subscription_id"], event_id)


@register("payment.dunning_d3")
def email_dunning_d3(payload: dict, event_id: str) -> None:
    """Sends a stronger overdue reminder at D+3."""
    from apps.notifications.tasks import send_payment_overdue_email

    # Re-uses the overdue email task — idempotent via Notification.get_or_create.
    send_payment_overdue_email.delay(payload["invoice_id"], event_id)


@register("renewal_invoice.created")
def register_renewal_charge(payload: dict, event_id: str) -> None:
    """
    Dispatches a new renewal invoice to Asaas for collection.
    Uses RegisterChargeCommand which is idempotent (skips if asaas_id already set).
    """
    from apps.billing.commands import RegisterChargeCommand
    from apps.billing.gateway.asaas_adapter import AsaasGateway

    try:
        RegisterChargeCommand(
            invoice_id=payload["invoice_id"],
            gateway=AsaasGateway(),
        ).execute()
    except Exception as exc:
        logger.error(
            "register_renewal_charge failed invoice_id=%s error=%s",
            payload.get("invoice_id"),
            exc,
        )


@register("invitation.created")
def email_invitation(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_invitation_email

    send_invitation_email.delay(payload["invitation_id"], event_id)


@register("invitation.accepted")
def log_invitation_accepted(payload: dict, event_id: str) -> None:
    logger.info(
        "invitation.accepted event_id=%s invitation_id=%s customer_id=%s user_id=%s",
        event_id,
        payload.get("invitation_id"),
        payload.get("customer_id"),
        payload.get("user_id"),
    )


@register("invitation.accepted")
def email_invitation_accepted(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_invitation_accepted_email

    send_invitation_accepted_email.delay(payload["invitation_id"], event_id)


@register("subscription.suspended")
def email_subscription_suspended(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_suspended_email

    send_subscription_suspended_email.delay(payload["subscription_id"], event_id)


@register("subscription.expired")
def email_subscription_expired(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_expired_email

    send_subscription_expired_email.delay(payload["subscription_id"], event_id)


@register("subscription.grace_period")
def email_grace_period(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_grace_period_email

    send_subscription_grace_period_email.delay(payload["subscription_id"], event_id)


@register("subscription.renewed")
def email_subscription_renewed(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_renewed_email

    send_subscription_renewed_email.delay(payload["subscription_id"], event_id)


@register("subscription.cancelled")
def email_subscription_cancelled(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_cancelled_email

    send_subscription_cancelled_email.delay(payload["subscription_id"], event_id)


@register("subscription.plan_changed")
def email_plan_changed(payload: dict, event_id: str) -> None:
    """Notifies the customer when a plan upgrade/downgrade completes."""
    from apps.notifications.tasks import send_plan_changed_email

    send_plan_changed_email.delay(payload["subscription_id"], event_id)


@register("subscription.expiring_soon")
def email_expiring_soon(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_expiring_soon_email

    send_subscription_expiring_soon_email.delay(
        payload["subscription_id"],
        event_id,
        payload.get("days_remaining", 3),
    )


@register("quota.warning")
def email_quota_warning(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_quota_warning_email

    send_quota_warning_email.delay(
        payload["customer_id"],
        event_id,
        payload.get("usage_pct", 80.0),
        payload.get("threshold", 80),
    )


# ── In-app notifications ──────────────────────────────────────────────────────
# Each handler creates a Notification(channel=IN_APP) so the bell icon in the
# dashboard shows real-time feedback without requiring an email client.
# The unique constraint (outbox_event_id, channel) prevents duplicates on retry.


def _in_app(event_id: str, customer_id: str, event_type: str, subject: str, body: str) -> None:
    from apps.notifications.models import Notification

    Notification.objects.get_or_create(
        outbox_event_id=event_id,
        channel=Notification.Channel.IN_APP,
        defaults={
            "event_type": event_type,
            "recipient": customer_id,
            "subject": subject,
            "body": body,
            "status": Notification.Status.PENDING,
        },
    )


@register("payment.processed")
def in_app_payment_confirmed(payload: dict, event_id: str) -> None:
    from apps.billing.models import Invoice

    try:
        invoice = Invoice.objects.get(pk=payload["invoice_id"])
    except Invoice.DoesNotExist:
        return
    _in_app(
        event_id,
        str(invoice.customer_id),
        "payment.processed",
        "Pagamento confirmado",
        f"Sua fatura de R$ {invoice.amount:.2f} foi paga com sucesso.",
    )


@register("payment.due_soon")
def in_app_payment_due_soon(payload: dict, event_id: str) -> None:
    days = payload.get("days_until_due", 3)
    amount = payload.get("amount", "")
    _in_app(
        event_id,
        payload["customer_id"],
        "payment.due_soon",
        f"Fatura vence em {days} {'dia' if days == 1 else 'dias'}",
        f"Sua fatura de R$ {amount} vence em {days} {'dia' if days == 1 else 'dias'}. Garanta que o pagamento seja efetuado.",
    )


@register("payment.dunning_d3")
def in_app_dunning_d3(payload: dict, event_id: str) -> None:
    days = payload.get("days_overdue", 3)
    amount = payload.get("amount", "")
    _in_app(
        event_id,
        payload["customer_id"],
        "payment.dunning_d3",
        f"Fatura vencida há {days} {'dia' if days == 1 else 'dias'}",
        f"Sua fatura de R$ {amount} está vencida há {days} dias. Regularize agora para evitar a suspensão da assinatura.",
    )


@register("payment.failed")
def in_app_payment_overdue(payload: dict, event_id: str) -> None:
    from apps.billing.models import Invoice

    try:
        invoice = Invoice.objects.get(pk=payload["invoice_id"])
    except Invoice.DoesNotExist:
        return
    _in_app(
        event_id,
        str(invoice.customer_id),
        "payment.failed",
        "Fatura vencida",
        f"Sua fatura de R$ {invoice.amount:.2f} está vencida. Regularize para evitar suspensão.",
    )


@register("subscription.expiring_soon")
def in_app_expiring_soon(payload: dict, event_id: str) -> None:
    days = payload.get("days_remaining", 3)
    _in_app(
        event_id,
        payload["customer_id"],
        "subscription.expiring_soon",
        f"Assinatura vence em {days} {'dia' if days == 1 else 'dias'}",
        "Renove sua assinatura para manter o acesso aos serviços.",
    )


@register("subscription.renewed")
def in_app_subscription_renewed(payload: dict, event_id: str) -> None:
    _in_app(
        event_id,
        payload["customer_id"],
        "subscription.renewed",
        "Assinatura renovada",
        "Sua assinatura foi renovada com sucesso.",
    )


@register("subscription.suspended")
def in_app_subscription_suspended(payload: dict, event_id: str) -> None:
    _in_app(
        event_id,
        payload["customer_id"],
        "subscription.suspended",
        "Assinatura suspensa",
        "Sua assinatura foi suspensa por falta de pagamento. Regularize para reativar o acesso.",
    )


@register("subscription.expired")
def in_app_subscription_expired(payload: dict, event_id: str) -> None:
    _in_app(
        event_id,
        payload["customer_id"],
        "subscription.expired",
        "Acesso encerrado",
        "Seu período de tolerância expirou. Assine novamente para retomar o acesso.",
    )


@register("subscription.grace_period")
def in_app_grace_period(payload: dict, event_id: str) -> None:
    _in_app(
        event_id,
        payload["customer_id"],
        "subscription.grace_period",
        "Assinatura em período de tolerância",
        "Sua assinatura venceu. Você tem 3 dias para renovar antes de perder o acesso.",
    )


@register("subscription.plan_changed")
def in_app_plan_changed(payload: dict, event_id: str) -> None:
    _in_app(
        event_id,
        payload["customer_id"],
        "subscription.plan_changed",
        "Plano alterado",
        "Seu plano foi alterado com sucesso.",
    )


@register("customer.suspended")
def in_app_customer_suspended(payload: dict, event_id: str) -> None:
    _in_app(
        event_id,
        payload["customer_id"],
        "customer.suspended",
        "Conta suspensa",
        "Sua conta foi suspensa por falta de pagamento. Regularize suas faturas para reativar.",
    )


@register("customer.reactivated")
def in_app_customer_reactivated(payload: dict, event_id: str) -> None:
    _in_app(
        event_id,
        payload["customer_id"],
        "customer.reactivated",
        "Conta reativada",
        "Sua conta foi reativada com sucesso. Todos os serviços estão disponíveis.",
    )


_service_label_map: dict[str, str] = {
    "chatwoot": "Chatwoot",
    "meta_whatsapp": "WhatsApp API Meta",
    "n8n": "n8n",
    "glpi": "GLPI Helpdesk",
    "zabbix": "Zabbix",
    "proxmox": "Proxmox VE",
    "truenas": "TrueNAS",
    "nextcloud": "Nextcloud",
    "aapanel": "AAPanel",
    "evolution_api": "Evolution API",
    "rustdesk": "RustDesk",
    "samba": "Samba",
    "windows-server": "Windows Server",
    "plone": "Plone CMS",
    "keycloak": "Keycloak",
    "tailscale": "Tailscale",
    "twenty_crm": "Twenty CRM",
    "papermark": "Papermark",
    "crowdsec": "CrowdSec",
}


@register("service.provisioned")
def in_app_service_provisioned(payload: dict, event_id: str) -> None:
    service_key = payload.get("service_key", "")
    label = _service_label_map.get(service_key, service_key)
    _in_app(
        event_id,
        payload["customer_id"],
        "service.provisioned",
        f"{label} provisionado",
        f"O serviço {label} foi implantado e está disponível no seu dashboard.",
    )


@register("user.registered")
def notify_admin_new_registration(payload: dict, event_id: str) -> None:
    """Sends the admin team an email when a new user self-registers."""
    from django.conf import settings

    from shared.email import send_html_email

    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", settings.DEFAULT_FROM_EMAIL)
    admin_url = build_frontend_url("/backoffice/customers")

    send_html_email(
        subject=f"Novo cadastro: {payload.get('company_name', payload.get('name', 'desconhecido'))} — PaperMoon",
        template_name="user_registered",
        context={
            "name": payload.get("name", ""),
            "email": payload.get("email", ""),
            "company_name": payload.get("company_name", ""),
            "phone": payload.get("phone", ""),
            "admin_url": admin_url,
        },
        recipient=admin_email,
    )
