import secrets
from uuid import uuid4

from django.db import models
from django.utils import timezone


class ApiKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="api_keys",
    )
    key = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "licensing_api_keys"

    def __str__(self) -> str:
        return f"ApiKey({self.customer_id} active={self.is_active})"

    def save(self, *args, **kwargs) -> None:
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class LicenseQuota(models.Model):
    customer = models.OneToOneField(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="quota",
    )
    max_api_calls = models.IntegerField(default=10000)
    used_api_calls = models.IntegerField(default=0)
    reset_at = models.DateTimeField()

    class Meta:
        db_table = "licensing_quotas"

    def __str__(self) -> str:
        return f"LicenseQuota({self.customer_id} {self.used_api_calls}/{self.max_api_calls})"


class DailyApiUsage(models.Model):
    """
    Daily snapshot of API calls per customer.
    Written by the snapshot_daily_api_usage beat task at 23:55 each day.
    Used to render usage trend charts in the client dashboard.
    """

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="daily_api_usage",
    )
    date = models.DateField(default=timezone.now)
    calls_count = models.IntegerField(default=0)

    class Meta:
        db_table = "licensing_daily_api_usage"
        unique_together = [("customer", "date")]
        ordering = ["date"]
        indexes = [models.Index(fields=["customer", "date"])]

    def __str__(self) -> str:
        return f"DailyApiUsage({self.customer_id} {self.date} calls={self.calls_count})"
