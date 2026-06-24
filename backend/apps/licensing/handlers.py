"""Licensing OutboxEvent handlers — registered in NotificationsConfig.ready()."""

import logging

from apps.notifications.registry import register

logger = logging.getLogger(__name__)


@register("customer.created")
def create_license_quota(payload: dict, event_id: str) -> None:
    from django.utils import timezone

    from apps.licensing.models import LicenseQuota

    LicenseQuota.objects.get_or_create(
        customer_id=payload["customer_id"],
        defaults={
            "max_api_calls": 10000,
            "used_api_calls": 0,
            "reset_at": _next_month_start(timezone.now()),
        },
    )


@register("subscription.created")
def sync_quota_from_subscription(payload: dict, event_id: str) -> None:
    """Update LicenseQuota.max_api_calls to match the subscription's Pricing.
    Called both on new subscriptions and after a plan change (ChangeSubscriptionPlanCommand
    fires subscription.created for the new subscription).
    """
    from apps.licensing.models import LicenseQuota
    from apps.subscriptions.models import Subscription

    subscription_id = payload.get("subscription_id")
    if not subscription_id:
        return

    try:
        sub = Subscription.objects.select_related("pricing").get(pk=subscription_id)
    except Subscription.DoesNotExist:
        logger.warning("sync_quota_from_subscription: subscription %s not found", subscription_id)
        return

    max_calls = sub.pricing.max_api_calls
    if max_calls and max_calls > 0:
        updated = LicenseQuota.objects.filter(customer_id=sub.customer_id).update(
            max_api_calls=max_calls
        )
        if updated:
            logger.info(
                "sync_quota_from_subscription customer_id=%s max_api_calls=%s",
                sub.customer_id,
                max_calls,
            )


@register("customer.suspended")
def deactivate_api_keys(payload: dict, event_id: str) -> None:
    from apps.licensing.models import ApiKey

    ApiKey.objects.filter(customer_id=payload["customer_id"]).update(is_active=False)


@register("customer.reactivated")
def reactivate_api_keys(payload: dict, event_id: str) -> None:
    from apps.licensing.models import ApiKey

    ApiKey.objects.filter(customer_id=payload["customer_id"]).update(is_active=True)


def _next_month_start(now):
    if now.month == 12:
        return now.replace(
            year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
