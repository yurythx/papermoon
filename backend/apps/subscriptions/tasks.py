from datetime import timedelta
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

GRACE_PERIOD_DAYS = 3


@shared_task
def scan_expiring_subscriptions() -> None:
    """
    Daily task.
    ACTIVE past expires_at → GRACE_PERIOD.
    GRACE_PERIOD past (expires_at + grace days) → EXPIRED + deprovision.
    """
    from apps.subscriptions.commands import ExpireSubscriptionCommand
    from apps.subscriptions.models import Subscription

    now = timezone.now()
    grace_deadline = now - timedelta(days=GRACE_PERIOD_DAYS)
    cmd = ExpireSubscriptionCommand()

    for sub_id in Subscription.objects.filter(
        status=Subscription.Status.ACTIVE, expires_at__lte=now
    ).values_list("id", flat=True):
        try:
            cmd.execute(sub_id)
        except Exception as exc:
            logger.error("scan_expiring_subscriptions active→grace sub_id=%s error=%s", sub_id, exc)

    for sub_id in Subscription.objects.filter(
        status=Subscription.Status.GRACE_PERIOD, expires_at__lte=grace_deadline
    ).values_list("id", flat=True):
        try:
            cmd.execute(sub_id)
        except Exception as exc:
            logger.error(
                "scan_expiring_subscriptions grace→expired sub_id=%s error=%s", sub_id, exc
            )


@shared_task
def generate_renewal_invoices() -> None:
    """
    Daily task (D-3 before expiry).
    Generates an Invoice for every active subscription expiring in the next 3 days
    that doesn't already have a pending invoice.
    The Asaas webhook closes the loop: payment confirmed → subscription renewed.
    """
    from datetime import timedelta

    from apps.subscriptions.models import Subscription
    from apps.subscriptions.renewal import GenerateRenewalInvoiceCommand

    now = timezone.now()
    window_start = now
    window_end = now + timedelta(days=3)
    cmd = GenerateRenewalInvoiceCommand()

    for sub_id in Subscription.objects.filter(
        status__in=[
            Subscription.Status.ACTIVE,
            Subscription.Status.TRIAL,
        ],
        expires_at__gte=window_start,
        expires_at__lt=window_end,
    ).values_list("id", flat=True):
        try:
            cmd.execute(sub_id)
        except Exception as exc:
            logger.error("generate_renewal_invoices sub_id=%s error=%s", sub_id, exc)


@shared_task
def scan_quota_warnings() -> None:
    """
    Daily task. Emits quota.warning OutboxEvents for customers whose
    used_api_calls has crossed the 80% or 90% threshold.
    One event per threshold per reset cycle — idempotency via OutboxEvent dedup is not used
    here since quotas reset monthly; crossing 80% again after a reset is a new event.
    """
    from apps.licensing.models import LicenseQuota
    from shared.models import OutboxEvent

    for quota in LicenseQuota.objects.select_related("customer").filter(max_api_calls__gt=0):
        pct = quota.used_api_calls / quota.max_api_calls * 100
        if pct < 80:
            continue

        threshold = 90 if pct >= 90 else 80
        OutboxEvent.objects.create(
            event_type="quota.warning",
            payload={
                "customer_id": str(quota.customer_id),
                "used_api_calls": quota.used_api_calls,
                "max_api_calls": quota.max_api_calls,
                "usage_pct": round(pct, 1),
                "threshold": threshold,
            },
        )
        logger.info(
            "scan_quota_warnings customer_id=%s pct=%.1f threshold=%s",
            quota.customer_id,
            pct,
            threshold,
        )


@shared_task
def scan_expiring_soon() -> None:
    """
    Daily task. Emits subscription.expiring_soon OutboxEvents for D-7, D-3, D-1.
    Each threshold window is exactly 1 day wide so a subscription matches once per threshold.
    """
    from apps.subscriptions.models import Subscription
    from shared.models import OutboxEvent

    now = timezone.now()
    for days in [7, 3, 1]:
        window_start = now + timedelta(days=days - 1)
        window_end = now + timedelta(days=days)
        for sub in Subscription.objects.filter(
            status=Subscription.Status.ACTIVE,
            expires_at__gte=window_start,
            expires_at__lt=window_end,
        ):
            OutboxEvent.objects.create(
                event_type="subscription.expiring_soon",
                payload={
                    "subscription_id": str(sub.id),
                    "customer_id": str(sub.customer_id),
                    "days_remaining": days,
                    "expires_at": sub.expires_at.isoformat(),
                },
            )
