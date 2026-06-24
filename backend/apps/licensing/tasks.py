import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def snapshot_daily_api_usage() -> None:
    """
    Snapshot current used_api_calls into DailyApiUsage for today.
    Runs at 23:55 via beat. Uses update_or_create so re-runs are safe.
    """
    from django.utils import timezone

    from apps.licensing.models import DailyApiUsage, LicenseQuota

    today = timezone.localdate()
    quotas = LicenseQuota.objects.select_related("customer").all()
    for quota in quotas:
        _obj, _created = DailyApiUsage.objects.update_or_create(
            customer=quota.customer,
            date=today,
            defaults={"calls_count": quota.used_api_calls},
        )
        logger.debug(
            "snapshot_daily_api_usage customer_id=%s date=%s calls=%s created=%s",
            quota.customer_id,
            today,
            quota.used_api_calls,
            _created,
        )
    logger.info("snapshot_daily_api_usage done total=%s", len(quotas))


@shared_task
def reset_quota_monthly() -> None:
    """Reset used_api_calls for all LicenseQuotas whose reset_at has passed."""
    from django.utils import timezone

    from apps.licensing.models import LicenseQuota

    now = timezone.now()
    expired = LicenseQuota.objects.filter(reset_at__lte=now)
    for quota in expired:
        quota.used_api_calls = 0
        if quota.reset_at.month == 12:
            quota.reset_at = quota.reset_at.replace(year=quota.reset_at.year + 1, month=1, day=1)
        else:
            quota.reset_at = quota.reset_at.replace(month=quota.reset_at.month + 1, day=1)
        quota.save()
        logger.info("reset_quota_monthly customer_id=%s", quota.customer_id)
