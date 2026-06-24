"""
Provisioning handlers registered on the shared OutboxEvent registry.
Each handler receives the event payload and dispatches to the correct
AbstractProvisioner based on service_key.

Imported by apps/notifications/handlers.py so they register at startup.
"""

import logging

from apps.notifications.registry import register
from apps.provisioning.registry import get_provisioner

logger = logging.getLogger(__name__)


def _emit_provisioned(customer_id: str, service_key: str) -> None:
    """Writes a service.provisioned OutboxEvent so notification handlers can react."""
    from shared.models import OutboxEvent

    OutboxEvent.objects.create(
        event_type="service.provisioned",
        payload={"customer_id": customer_id, "service_key": service_key},
    )


def _alert_telegram(message: str) -> None:
    """Sends a Telegram message to the ops alert channel. No-ops if not configured."""
    from django.conf import settings
    import requests

    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_ALERT_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception as exc:
        logger.warning("telegram alert failed: %s", exc)


@register("subscription.created")
def provision_services(payload: dict, event_id: str) -> None:
    from django.utils import timezone

    from apps.subscriptions.models import ServiceAccess

    license_id = payload.get("license_id")
    customer_id = payload.get("customer_id")
    service_keys = payload.get("service_keys", [])

    for service_key in service_keys:
        provisioner = get_provisioner(service_key)
        if not provisioner:
            logger.warning("provision_services unknown service_key=%s", service_key)
            continue

        try:
            service_access = ServiceAccess.objects.get(
                license_id=license_id, service_key=service_key
            )
        except ServiceAccess.DoesNotExist:
            logger.error(
                "provision_services ServiceAccess not found license_id=%s service_key=%s",
                license_id,
                service_key,
            )
            continue

        try:
            external_id = provisioner.provision(
                customer_id=customer_id,
                service_access_id=str(service_access.id),
                config=service_access.config,
            )
            service_access.external_id = external_id
            service_access.status = ServiceAccess.Status.ACTIVE
            service_access.provisioned_at = timezone.now()
            service_access.error = None
            _emit_provisioned(customer_id, service_key)
        except Exception as exc:
            service_access.status = ServiceAccess.Status.FAILED
            service_access.error = str(exc)
            logger.error(
                "provision_services failed service_key=%s customer_id=%s error=%s",
                service_key,
                customer_id,
                exc,
            )
            _alert_telegram(
                f"<b>Provisioning failed</b>\n"
                f"Service: <code>{service_key}</code>\n"
                f"Customer: <code>{customer_id}</code>\n"
                f"Error: <code>{exc}</code>"
            )

        service_access.save(
            update_fields=["external_id", "status", "provisioned_at", "error", "updated_at"]
        )


@register("subscription.suspended")
def suspend_services(payload: dict, event_id: str) -> None:
    _act_on_services(payload, action="suspend")


@register("subscription.expired")
def deprovision_services(payload: dict, event_id: str) -> None:
    _act_on_services(payload, action="deprovision")


@register("subscription.cancelled")
def deprovision_services_on_cancel(payload: dict, event_id: str) -> None:
    _act_on_services(payload, action="deprovision")


@register("subscription.renewed")
def reactivate_services(payload: dict, event_id: str) -> None:
    from apps.subscriptions.models import ServiceAccess

    license_id = payload.get("license_id") or _license_id_from_subscription(
        payload.get("subscription_id")
    )
    customer_id = payload.get("customer_id")
    if not license_id:
        return

    for sa in ServiceAccess.objects.filter(
        license_id=license_id, status=ServiceAccess.Status.SUSPENDED
    ):
        provisioner = get_provisioner(sa.service_key)
        if not provisioner:
            continue
        try:
            provisioner.reactivate(external_id=sa.external_id or "", customer_id=customer_id)
            sa.status = ServiceAccess.Status.ACTIVE
            sa.suspended_at = None
            sa.save(update_fields=["status", "suspended_at", "updated_at"])
        except Exception as exc:
            logger.error("reactivate_services failed service_key=%s error=%s", sa.service_key, exc)


@register("subscription.grace_period")
def notify_grace_period(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_grace_period_email

    send_subscription_grace_period_email.delay(payload["subscription_id"], event_id)


@register("subscription.expiring_soon")
def notify_expiring_soon(payload: dict, event_id: str) -> None:
    from apps.notifications.tasks import send_subscription_expiring_soon_email

    send_subscription_expiring_soon_email.delay(payload["subscription_id"], event_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _act_on_services(payload: dict, action: str) -> None:
    from apps.subscriptions.models import ServiceAccess

    license_id = payload.get("license_id")
    customer_id = payload.get("customer_id")
    service_keys = payload.get("service_keys", [])

    if not license_id or not service_keys:
        return

    for service_key in service_keys:
        provisioner = get_provisioner(service_key)
        if not provisioner:
            logger.warning("_act_on_services unknown service_key=%s", service_key)
            continue

        try:
            sa = ServiceAccess.objects.get(license_id=license_id, service_key=service_key)
        except ServiceAccess.DoesNotExist:
            continue

        try:
            getattr(provisioner, action)(external_id=sa.external_id or "", customer_id=customer_id)
        except Exception as exc:
            logger.error(
                "_act_on_services action=%s service_key=%s error=%s", action, service_key, exc
            )


@register("subscription.created")
def sync_quota_on_create(payload: dict, event_id: str) -> None:
    """
    Set LicenseQuota limits from the Pricing when a subscription is first created.
    Creates the quota record if it doesn't exist yet (idempotent).
    """
    _sync_quota(payload.get("subscription_id"))


@register("subscription.renewed")
def sync_quota_on_renewal(payload: dict, event_id: str) -> None:
    """Keep quota limits current when the customer renews (plan may have changed)."""
    _sync_quota(payload.get("subscription_id"))


def _sync_quota(subscription_id: str | None) -> None:
    if not subscription_id:
        return

    from django.utils import timezone

    from apps.licensing.models import LicenseQuota
    from apps.subscriptions.models import Subscription

    try:
        sub = Subscription.objects.select_related("pricing").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        return

    pricing = sub.pricing
    quota, created = LicenseQuota.objects.get_or_create(
        customer_id=sub.customer_id,
        defaults={
            "max_api_calls": pricing.max_api_calls,
            "used_api_calls": 0,
            "reset_at": timezone.now().replace(day=1) + __import__("datetime").timedelta(days=32),
        },
    )

    if not created:
        # Update limits to match the current pricing — don't reset used_api_calls
        quota.max_api_calls = pricing.max_api_calls
        quota.save(update_fields=["max_api_calls"])

    logger.info(
        "_sync_quota customer_id=%s max_api_calls=%s",
        sub.customer_id,
        pricing.max_api_calls,
    )


@register("customer.suspended")
def cascade_suspend_subscriptions(payload: dict, event_id: str) -> None:
    """
    When a tenant is suspended, all their active subscriptions are suspended too.
    Each SuspendSubscriptionCommand emits its own subscription.suspended event,
    which triggers the per-service provisioner chain.
    """
    from apps.subscriptions.commands import SuspendSubscriptionCommand
    from apps.subscriptions.models import Subscription

    customer_id = payload.get("customer_id")
    cmd = SuspendSubscriptionCommand()

    for sub_id in Subscription.objects.filter(
        customer_id=customer_id,
        status__in=[
            Subscription.Status.ACTIVE,
            Subscription.Status.TRIAL,
            Subscription.Status.GRACE_PERIOD,
        ],
    ).values_list("id", flat=True):
        try:
            cmd.execute(sub_id, reason="customer_suspended")
        except Exception as exc:
            logger.error("cascade_suspend_subscriptions sub_id=%s error=%s", sub_id, exc)


@register("customer.reactivated")
def cascade_reactivate_subscriptions(payload: dict, event_id: str) -> None:
    """
    When a tenant is reactivated, subscriptions that were suspended due to
    customer suspension (not due to payment) are also reactivated.
    """
    from apps.subscriptions.commands import RenewSubscriptionCommand
    from apps.subscriptions.models import Subscription

    customer_id = payload.get("customer_id")
    cmd = RenewSubscriptionCommand()

    for sub_id in Subscription.objects.filter(
        customer_id=customer_id,
        status=Subscription.Status.SUSPENDED,
    ).values_list("id", flat=True):
        try:
            cmd.execute(sub_id)
        except Exception as exc:
            logger.error("cascade_reactivate_subscriptions sub_id=%s error=%s", sub_id, exc)


@register("service_access.provision")
def provision_single_service(payload: dict, event_id: str) -> None:
    """Handles on-demand provisioning for a single ServiceAccess (added after subscription creation)."""
    from django.utils import timezone

    from apps.subscriptions.models import ServiceAccess

    service_access_id = payload.get("service_access_id")
    customer_id = payload.get("customer_id")
    service_key = payload.get("service_key")

    provisioner = get_provisioner(service_key)
    if not provisioner:
        logger.warning("provision_single_service unknown service_key=%s", service_key)
        return

    try:
        sa = ServiceAccess.objects.get(pk=service_access_id)
    except ServiceAccess.DoesNotExist:
        logger.error("provision_single_service ServiceAccess not found id=%s", service_access_id)
        return

    try:
        external_id = provisioner.provision(
            customer_id=customer_id,
            service_access_id=service_access_id,
            config=sa.config,
        )
        sa.external_id = external_id
        sa.status = ServiceAccess.Status.ACTIVE
        sa.provisioned_at = timezone.now()
        sa.error = None
    except Exception as exc:
        sa.status = ServiceAccess.Status.FAILED
        sa.error = str(exc)
        logger.error("provision_single_service failed service_key=%s error=%s", service_key, exc)

    sa.save(update_fields=["external_id", "status", "provisioned_at", "error", "updated_at"])


@register("service_access.deprovision")
def deprovision_single_service(payload: dict, event_id: str) -> None:
    """Handles on-demand deprovisioning for a single ServiceAccess (removed by admin)."""
    service_key = payload.get("service_key")
    external_id = payload.get("external_id") or ""
    customer_id = payload.get("customer_id")

    provisioner = get_provisioner(service_key)
    if not provisioner:
        logger.warning("deprovision_single_service unknown service_key=%s", service_key)
        return

    try:
        provisioner.deprovision(external_id=external_id, customer_id=customer_id)
    except Exception as exc:
        logger.error("deprovision_single_service failed service_key=%s error=%s", service_key, exc)


def _license_id_from_subscription(subscription_id: str | None) -> str | None:
    if not subscription_id:
        return None
    from apps.subscriptions.models import License

    try:
        return str(
            License.objects.values_list("id", flat=True).get(subscription_id=subscription_id)
        )
    except License.DoesNotExist:
        return None
