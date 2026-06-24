from datetime import timedelta
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.local")

app = Celery("papermoon")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.timezone = "America/Sao_Paulo"
app.conf.enable_utc = True

app.conf.beat_schedule = {
    # Infra
    "cleanup_old_outbox_events": {
        "task": "shared.tasks.cleanup_old_outbox_events",
        "schedule": crontab(hour=0, minute=0),
    },
    # Billing
    "scan_overdue_invoices": {
        "task": "apps.billing.tasks.scan_overdue_invoices",
        "schedule": crontab(hour=0, minute=0),
    },
    "scan_upcoming_invoices": {
        "task": "apps.billing.tasks.scan_upcoming_invoices",
        "schedule": crontab(hour=9, minute=0),
    },
    "process_dunning": {
        "task": "apps.billing.tasks.process_dunning",
        "schedule": crontab(hour=10, minute=0),
    },
    # Notifications — single OutboxEvent dispatcher (replaces licensing + support consumers)
    "process_outbox_events": {
        "task": "apps.notifications.tasks.process_outbox_events",
        "schedule": timedelta(seconds=5),
    },
    # Licensing
    "snapshot_daily_api_usage": {
        "task": "apps.licensing.tasks.snapshot_daily_api_usage",
        "schedule": crontab(hour=23, minute=55),
    },
    "reset_quota_monthly": {
        "task": "apps.licensing.tasks.reset_quota_monthly",
        "schedule": crontab(hour=1, minute=0),
    },
    # Subscriptions
    "scan_expiring_subscriptions": {
        "task": "apps.subscriptions.tasks.scan_expiring_subscriptions",
        "schedule": crontab(hour=0, minute=30),
    },
    "scan_expiring_soon": {
        "task": "apps.subscriptions.tasks.scan_expiring_soon",
        "schedule": crontab(hour=8, minute=0),
    },
    "generate_renewal_invoices": {
        "task": "apps.subscriptions.tasks.generate_renewal_invoices",
        "schedule": crontab(hour=9, minute=0),
    },
    "scan_quota_warnings": {
        "task": "apps.subscriptions.tasks.scan_quota_warnings",
        "schedule": crontab(hour=10, minute=0),
    },
}
