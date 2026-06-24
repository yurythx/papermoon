import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from shared.email import send_html_email
from shared.public_urls import build_frontend_url, sanitize_payment_url

logger = logging.getLogger(__name__)

_MAX_RETRIES = 5


@shared_task
def process_outbox_events() -> None:
    """
    Single OutboxEvent consumer.

    Routes each unprocessed event to all registered handlers by event_type.
    Uses select_for_update(skip_locked=True) so multiple Celery workers can run
    concurrently without processing the same event twice.
    Handlers receive (payload, event_id) — event_id enables idempotency at the handler level.
    """
    from apps.notifications.registry import get_handlers
    from shared.models import OutboxEvent

    with transaction.atomic():
        events = (
            OutboxEvent.objects.select_for_update(skip_locked=True)
            .filter(processed=False, retry_count__lt=_MAX_RETRIES)
            .order_by("created_at")[:50]
        )

        for event in events:
            handlers = get_handlers(event.event_type)
            if not handlers:
                event.processed = True
                event.processed_at = timezone.now()
                event.save()
                continue

            try:
                for handler in handlers:
                    handler(event.payload, str(event.id))
                event.processed = True
                event.processed_at = timezone.now()
            except Exception as exc:
                event.retry_count += 1
                event.last_error = str(exc)
                if event.retry_count >= _MAX_RETRIES:
                    event.failed_at = timezone.now()
                    logger.error(
                        "notifications.process_outbox_events max_retries "
                        "event_id=%s event_type=%s error=%s",
                        event.id,
                        event.event_type,
                        exc,
                    )
            event.save()


# ---------------------------------------------------------------------------
# Email delivery tasks
# ---------------------------------------------------------------------------


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_payment_due_soon_email(self, invoice_id: str, outbox_event_id: str) -> None:

    from apps.billing.models import Invoice
    from apps.notifications.models import Notification

    try:
        invoice = Invoice.objects.select_related("customer").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.warning("send_payment_due_soon_email invoice not found id=%s", invoice_id)
        return

    recipient = _owner_email(invoice.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Fatura de R$ {invoice.amount} vence em 3 dias"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "payment.due_soon",
            "recipient": recipient,
            "subject": subject,
            "body": f"Fatura de R$ {invoice.amount} vence em {invoice.due_date}.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {invoice.customer.company_name}!",
                    f"Sua fatura de R$ {invoice.amount} vence em {invoice.due_date.strftime('%d/%m/%Y')} (em 3 dias).",
                    "Certifique-se de que o pagamento seja efetuado para evitar a suspensão dos serviços.",
                ],
                "cta_link": build_frontend_url("/dashboard/invoices"),
                "cta_label": "Ver faturas",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error("send_payment_due_soon_email failed invoice_id=%s error=%s", invoice_id, exc)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_payment_overdue_email(self, invoice_id: str, outbox_event_id: str) -> None:

    from apps.billing.models import Invoice
    from apps.notifications.models import Notification

    try:
        invoice = Invoice.objects.select_related("customer").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.warning("send_payment_overdue_email invoice not found id=%s", invoice_id)
        return

    recipient = _owner_email(invoice.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Fatura vencida — R$ {invoice.amount}"
    invoices_link = build_frontend_url("/dashboard/invoices")

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "payment.failed",
            "recipient": recipient,
            "subject": subject,
            "body": f"Fatura de R$ {invoice.amount} vencida em {invoice.due_date}.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="payment_failed",
            context={
                "company_name": invoice.customer.company_name,
                "amount": invoice.amount,
                "due_date": invoice.due_date.strftime("%d/%m/%Y"),
                "invoices_link": invoices_link,
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error("send_payment_overdue_email failed invoice_id=%s error=%s", invoice_id, exc)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_payment_confirmed_email(self, invoice_id: str, outbox_event_id: str) -> None:

    from apps.billing.models import Invoice
    from apps.notifications.models import Notification

    try:
        invoice = Invoice.objects.select_related("customer").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        return

    recipient = _owner_email(invoice.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Pagamento confirmado — R$ {invoice.amount}"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "payment.processed",
            "recipient": recipient,
            "subject": subject,
            "body": f"Pagamento de R$ {invoice.amount} confirmado.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {invoice.customer.company_name}!",
                    f"Seu pagamento de R$ {invoice.amount} foi confirmado. Obrigado por manter sua assinatura em dia!",
                ],
                "cta_link": build_frontend_url("/dashboard/invoices"),
                "cta_label": "Ver faturas",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error("send_payment_confirmed_email failed invoice_id=%s error=%s", invoice_id, exc)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_customer_cancelled_email(self, customer_id: str, outbox_event_id: str) -> None:
    from apps.customers.models import Customer, CustomerProfile
    from apps.notifications.models import Notification

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return

    profile = (
        CustomerProfile.objects.filter(customer=customer, role="owner")
        .select_related("user")
        .first()
    )
    if not profile:
        return

    recipient = profile.user.email
    subject = "[PaperMoon] Sua assinatura foi cancelada"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "customer.cancelled",
            "recipient": recipient,
            "subject": subject,
            "body": "Sua assinatura da PaperMoon foi cancelada.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {customer.company_name}!",
                    "Sua assinatura da PaperMoon foi cancelada.",
                    "Se isso foi um engano, entre em contato com nosso suporte o quanto antes.",
                ],
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error(
            "send_customer_cancelled_email failed customer_id=%s error=%s", customer_id, exc
        )
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_invitation_email(self, invitation_id: str, outbox_event_id: str) -> None:

    from apps.customers.models import Invitation
    from apps.notifications.models import Notification

    try:
        invitation = Invitation.objects.select_related("customer", "invited_by").get(
            pk=invitation_id
        )
    except Invitation.DoesNotExist:
        logger.warning("send_invitation_email invitation not found id=%s", invitation_id)
        return

    accept_link = build_frontend_url("/invite/accept", params={"token": invitation.token})
    inviter_name = (
        invitation.invited_by.get_full_name() or invitation.invited_by.email
        if invitation.invited_by
        else invitation.customer.company_name
    )
    subject = f"[PaperMoon] {inviter_name} te convidou para {invitation.customer.company_name}"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "invitation.created",
            "recipient": invitation.email,
            "subject": subject,
            "body": f"Convite de {inviter_name} para {invitation.customer.company_name}.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="invitation",
            context={
                "invited_by": inviter_name,
                "company_name": invitation.customer.company_name,
                "expiry_hours": 168,  # 7 days
                "accept_link": accept_link,
            },
            recipient=invitation.email,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error("send_invitation_email failed invitation_id=%s error=%s", invitation_id, exc)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_grace_period_email(self, subscription_id: str, outbox_event_id: str) -> None:

    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Sua licença {sub.product.name} entrou em período de tolerância"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.grace_period",
            "recipient": recipient,
            "subject": subject,
            "body": f"Licença {sub.product.name} em período de tolerância.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Sua licença do produto {sub.product.name} venceu, mas você ainda tem acesso por mais 3 dias.",
                    "Renove agora para não perder o acesso aos seus serviços.",
                ],
                "cta_link": build_frontend_url("/dashboard/subscriptions"),
                "cta_label": "Renovar agora",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_expiring_soon_email(
    self, subscription_id: str, outbox_event_id: str, days_remaining: int = 3
) -> None:

    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    day_label = f"{days_remaining} dia" if days_remaining == 1 else f"{days_remaining} dias"
    subject = f"[PaperMoon] Sua licença {sub.product.name} vence em {day_label}"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.expiring_soon",
            "recipient": recipient,
            "subject": subject,
            "body": f"Licença {sub.product.name} vence em {day_label}.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Sua licença do produto {sub.product.name} vence em "
                    f"{sub.expires_at.strftime('%d/%m/%Y')} ({day_label}).",
                    "Renove antes do vencimento para manter o acesso contínuo aos seus serviços.",
                ],
                "cta_link": build_frontend_url("/dashboard/subscriptions"),
                "cta_label": "Renovar agora",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_quota_warning_email(
    self,
    customer_id: str,
    outbox_event_id: str,
    usage_pct: float,
    threshold: int,
) -> None:

    from apps.customers.models import Customer
    from apps.notifications.models import Notification

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return

    recipient = _owner_email(customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Alerta: {threshold}% da sua cota de API utilizada"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "quota.warning",
            "recipient": recipient,
            "subject": subject,
            "body": f"{usage_pct:.1f}% da cota mensal utilizada.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {customer.company_name}!",
                    f"Você já utilizou {usage_pct:.1f}% da sua cota mensal de chamadas de API.",
                    "Quando a cota for esgotada, as chamadas serão bloqueadas até o próximo ciclo.",
                ],
                "cta_link": build_frontend_url("/dashboard/api-keys"),
                "cta_label": "Ver consumo",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_renewed_email(self, subscription_id: str, outbox_event_id: str) -> None:

    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Assinatura {sub.product.name} renovada"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.renewed",
            "recipient": recipient,
            "subject": subject,
            "body": f"Assinatura {sub.product.name} renovada.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Sua assinatura do produto {sub.product.name} foi renovada com sucesso.",
                    f"Acesso garantido até {sub.expires_at.strftime('%d/%m/%Y')}.",
                ],
                "cta_link": build_frontend_url("/dashboard/subscriptions"),
                "cta_label": "Ver assinaturas",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_cancelled_email(self, subscription_id: str, outbox_event_id: str) -> None:
    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Assinatura {sub.product.name} cancelada"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.cancelled",
            "recipient": recipient,
            "subject": subject,
            "body": f"Assinatura {sub.product.name} cancelada.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Sua assinatura do produto {sub.product.name} foi cancelada.",
                    "Se precisar reativar ou tiver dúvidas, entre em contato com o suporte.",
                ],
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_plan_changed_email(self, subscription_id: str, outbox_event_id: str) -> None:

    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product", "pricing").get(
            pk=subscription_id
        )
    except Subscription.DoesNotExist:
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Plano alterado para {sub.product.name}"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.plan_changed",
            "recipient": recipient,
            "subject": subject,
            "body": f"Plano alterado para {sub.product.name}.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Seu plano foi alterado para {sub.product.name} "
                    f"({sub.pricing.get_billing_cycle_display()} — R$ {sub.pricing.amount}).",
                    f"Novo acesso garantido até {sub.expires_at.strftime('%d/%m/%Y')}.",
                ],
                "cta_link": build_frontend_url("/dashboard/subscriptions"),
                "cta_label": "Ver assinaturas",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_suspended_email(self, subscription_id: str, outbox_event_id: str) -> None:

    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Assinatura {sub.product.name} suspensa"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.suspended",
            "recipient": recipient,
            "subject": subject,
            "body": f"Assinatura {sub.product.name} suspensa por falta de pagamento.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Sua assinatura do produto {sub.product.name} foi suspensa por falta de pagamento.",
                    "Regularize sua situação para reativar o acesso aos serviços.",
                ],
                "cta_link": build_frontend_url("/dashboard/invoices"),
                "cta_label": "Ver faturas",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_expired_email(self, subscription_id: str, outbox_event_id: str) -> None:

    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Acesso ao {sub.product.name} encerrado"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.expired",
            "recipient": recipient,
            "subject": subject,
            "body": f"Acesso ao {sub.product.name} encerrado.",
        },
    )
    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Seu período de tolerância expirou e o acesso ao {sub.product.name} foi encerrado.",
                    "Para reativar, assine novamente pelo painel.",
                ],
                "cta_link": build_frontend_url("/dashboard/subscriptions"),
                "cta_label": "Assinar novamente",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_customer_suspended_email(self, customer_id: str, outbox_event_id: str) -> None:

    from apps.customers.models import Customer
    from apps.notifications.models import Notification

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return

    recipient = _owner_email(customer)
    if not recipient:
        return

    subject = "[PaperMoon] Sua conta foi suspensa"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "customer.suspended",
            "recipient": recipient,
            "subject": subject,
            "body": f"A conta {customer.company_name} foi suspensa.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {customer.company_name}!",
                    "Sua conta na PaperMoon foi suspensa por falta de pagamento.",
                    "Regularize suas faturas em aberto para reativar o acesso aos serviços.",
                ],
                "cta_link": build_frontend_url("/dashboard/invoices"),
                "cta_label": "Ver faturas",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error(
            "send_customer_suspended_email failed customer_id=%s error=%s", customer_id, exc
        )
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_customer_reactivated_email(self, customer_id: str, outbox_event_id: str) -> None:

    from apps.customers.models import Customer
    from apps.notifications.models import Notification

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return

    recipient = _owner_email(customer)
    if not recipient:
        return

    subject = "[PaperMoon] Sua conta foi reativada"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "customer.reactivated",
            "recipient": recipient,
            "subject": subject,
            "body": f"A conta {customer.company_name} foi reativada.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {customer.company_name}!",
                    "Sua conta na PaperMoon foi reativada com sucesso.",
                    "Você já pode utilizar todos os serviços normalmente.",
                ],
                "cta_link": build_frontend_url("/dashboard"),
                "cta_label": "Acessar painel",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error(
            "send_customer_reactivated_email failed customer_id=%s error=%s", customer_id, exc
        )
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_invitation_accepted_email(self, invitation_id: str, outbox_event_id: str) -> None:

    from apps.customers.models import Invitation
    from apps.notifications.models import Notification

    try:
        invitation = Invitation.objects.select_related("customer").get(pk=invitation_id)
    except Invitation.DoesNotExist:
        logger.warning("send_invitation_accepted_email invitation not found id=%s", invitation_id)
        return

    recipient = invitation.email
    company_name = invitation.customer.company_name
    subject = f"[PaperMoon] Bem-vindo(a) a {company_name}!"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "invitation.accepted",
            "recipient": recipient,
            "subject": subject,
            "body": f"Você entrou para a equipe de {company_name} na PaperMoon.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá! Você foi adicionado(a) à equipe de {company_name}.",
                    "Acesse o painel para começar a usar a plataforma.",
                ],
                "cta_link": build_frontend_url("/login"),
                "cta_label": "Acessar painel",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error(
            "send_invitation_accepted_email failed invitation_id=%s error=%s", invitation_id, exc
        )
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_subscription_created_email(self, subscription_id: str, outbox_event_id: str) -> None:

    from apps.notifications.models import Notification
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("customer", "product").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        logger.warning("send_subscription_created_email sub not found id=%s", subscription_id)
        return

    recipient = _owner_email(sub.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] {sub.product.name} ativado com sucesso!"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "subscription.created",
            "recipient": recipient,
            "subject": subject,
            "body": f"{sub.product.name} ativado para {sub.customer.company_name}.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {sub.customer.company_name}!",
                    f"Seu serviço {sub.product.name} foi ativado com sucesso.",
                    "Acesse o painel para acompanhar seus contratos e serviços.",
                ],
                "cta_link": build_frontend_url("/dashboard/subscriptions"),
                "cta_label": "Ver meus contratos",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error(
            "send_subscription_created_email failed sub_id=%s error=%s", subscription_id, exc
        )
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_customer_created_email(self, customer_id: str, outbox_event_id: str) -> None:

    from apps.customers.models import Customer
    from apps.notifications.models import Notification

    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        logger.warning("send_customer_created_email customer not found id=%s", customer_id)
        return

    recipient = _owner_email(customer)
    if not recipient:
        return

    subject = "[PaperMoon] Bem-vindo(a) à plataforma!"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "customer.created",
            "recipient": recipient,
            "subject": subject,
            "body": f"Conta criada para {customer.company_name}.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {customer.company_name}!",
                    "Sua conta foi criada com sucesso na PaperMoon.",
                    "Acesse o painel para ativar seus serviços e gerenciar sua equipe.",
                ],
                "cta_link": build_frontend_url("/dashboard"),
                "cta_label": "Acessar o painel",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error("send_customer_created_email failed customer_id=%s error=%s", customer_id, exc)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_invoice_ready_email(self, invoice_id: str, outbox_event_id: str) -> None:
    """
    Sent when Asaas confirms the charge was created and payment_url is available.
    Gives the client a direct link to pay — this is the primary payment CTA in the
    admin-managed model where no self-serve checkout exists.
    """

    from apps.billing.models import Invoice
    from apps.notifications.models import Notification

    try:
        invoice = Invoice.objects.select_related("customer").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        logger.warning("send_invoice_ready_email invoice not found id=%s", invoice_id)
        return

    payment_link = sanitize_payment_url(invoice.payment_url)
    if not payment_link:
        # Asaas didn't return a URL (e.g. sandbox without key) — fall back to portal.
        payment_link = build_frontend_url("/dashboard/invoices")

    recipient = _owner_email(invoice.customer)
    if not recipient:
        return

    subject = f"[PaperMoon] Fatura disponível — R$ {invoice.amount} vence em {invoice.due_date.strftime('%d/%m/%Y')}"

    notification, created = Notification.objects.get_or_create(
        outbox_event_id=outbox_event_id,
        channel=Notification.Channel.EMAIL,
        defaults={
            "event_type": "charge.registered",
            "recipient": recipient,
            "subject": subject,
            "body": f"Fatura de R$ {invoice.amount} disponível para pagamento.",
        },
    )

    if not created and notification.status == Notification.Status.SENT:
        return

    billing_type_label = {
        "BOLETO": "Boleto bancário",
        "PIX": "Pix",
        "CREDIT_CARD": "Cartão de crédito",
    }.get(invoice.billing_type, invoice.billing_type)

    try:
        send_html_email(
            subject=subject,
            template_name="notification",
            context={
                "subject": subject,
                "body_lines": [
                    f"Olá, {invoice.customer.company_name}!",
                    f"Uma nova fatura de R$ {invoice.amount} está disponível para pagamento.",
                    f"Forma de pagamento: {billing_type_label}.",
                    f"Vencimento: {invoice.due_date.strftime('%d/%m/%Y')}.",
                    "Clique no botão abaixo para efetuar o pagamento.",
                ],
                "cta_link": payment_link,
                "cta_label": "Pagar agora",
            },
            recipient=recipient,
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save()
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.error = str(exc)
        notification.save()
        logger.error("send_invoice_ready_email failed invoice_id=%s error=%s", invoice_id, exc)
        raise self.retry(exc=exc) from exc


def _owner_email(customer) -> str | None:
    from apps.customers.models import CustomerProfile

    profile = (
        CustomerProfile.objects.filter(customer=customer, role="owner")
        .select_related("user")
        .first()
    )
    return profile.user.email if profile else None


