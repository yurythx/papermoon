import calendar
import datetime
from decimal import Decimal
from uuid import UUID

from django.db.models import DecimalField, Q, QuerySet, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone

from apps.billing.models import Invoice

_ZERO = Decimal("0")
_DECIMAL_FIELD = DecimalField(max_digits=12, decimal_places=2)

# Exclude soft-deleted invoices in every query.
_ACTIVE = Q(deleted_at__isnull=True)


def get_financial_metrics(customer_id: UUID) -> dict:
    qs = Invoice.objects.filter(_ACTIVE, customer_id=customer_id)
    return {
        "total_paid": qs.filter(status=Invoice.Status.PAID).aggregate(
            v=Coalesce(Sum("amount"), _ZERO, output_field=_DECIMAL_FIELD)
        )["v"],
        "total_pending": qs.filter(status=Invoice.Status.PENDING).aggregate(
            v=Coalesce(Sum("amount"), _ZERO, output_field=_DECIMAL_FIELD)
        )["v"],
        "total_overdue": qs.filter(status=Invoice.Status.OVERDUE).aggregate(
            v=Coalesce(Sum("amount"), _ZERO, output_field=_DECIMAL_FIELD)
        )["v"],
    }


def list_invoices(customer_id: UUID, filters: dict | None = None) -> QuerySet:
    qs = Invoice.objects.filter(_ACTIVE, customer_id=customer_id).order_by("-created_at")
    if filters and (status := filters.get("status")):
        qs = qs.filter(status=status)
    return qs


def list_all_invoices(
    *,
    status: str | None = None,
    invoice_type: str | None = None,
    customer_id: str | None = None,
) -> QuerySet:
    """Admin-side invoice listing with optional filters. Excludes soft-deleted records."""
    qs = Invoice.objects.select_related("customer").filter(_ACTIVE).order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    if invoice_type:
        qs = qs.filter(invoice_type=invoice_type)
    if customer_id:
        qs = qs.filter(customer_id=customer_id)
    return qs


def get_mrr_metrics() -> dict:
    """
    Platform-wide MRR/ARR for the admin dashboard.

    MRR  = sum of all paid invoices in the current calendar month.
    ARR  = MRR * 12  (simplified; real ARR would use subscription intervals).
    Revenue by month = last 12 months of paid revenue, for the trend chart.
    Active customers = customers not cancelled and not soft-deleted.
    New customers    = created in current calendar month.
    Churn            = cancelled this month.
    Churn rate       = churned / (active + churned) * 100.
    Revenue by plan  = sum of paid invoices this month grouped by product name.
    At-risk count    = suspended customers where updated_at > 7 days ago.
    """
    from django.db.models import Count

    from apps.customers.models import Customer

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    _, last_day = calendar.monthrange(now.year, now.month)
    month_end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    paid_this_month = Invoice.objects.filter(
        _ACTIVE,
        status=Invoice.Status.PAID,
        updated_at__range=(month_start, month_end),
    )
    mrr: Decimal = paid_this_month.aggregate(
        v=Coalesce(Sum("amount"), _ZERO, output_field=_DECIMAL_FIELD)
    )["v"]

    # Monthly revenue trend — last 12 months
    twelve_months_ago = (now - datetime.timedelta(days=365)).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    monthly_revenue = (
        Invoice.objects.filter(
            _ACTIVE,
            status=Invoice.Status.PAID,
            updated_at__gte=twelve_months_ago,
        )
        .annotate(month=TruncMonth("updated_at"))
        .values("month")
        .annotate(revenue=Coalesce(Sum("amount"), _ZERO, output_field=_DECIMAL_FIELD))
        .order_by("month")
    )

    active_customers = Customer.objects.filter(
        deleted_at__isnull=True,
        status=Customer.Status.ACTIVE,
    ).count()

    new_customers = Customer.objects.filter(
        created_at__range=(month_start, month_end),
    ).count()

    churned_customers = Customer.objects.filter(
        status=Customer.Status.CANCELLED,
        updated_at__range=(month_start, month_end),
    ).count()

    churn_denominator = active_customers + churned_customers
    churn_rate = round(churned_customers / churn_denominator * 100, 1) if churn_denominator else 0.0

    # Revenue by plan — join paid invoices this month with subscription → product
    revenue_by_plan_qs = (
        Invoice.objects.filter(
            _ACTIVE,
            status=Invoice.Status.PAID,
            updated_at__range=(month_start, month_end),
            subscription__isnull=False,
        )
        .values("subscription__product__name")
        .annotate(
            revenue=Coalesce(Sum("amount"), _ZERO, output_field=_DECIMAL_FIELD),
            customer_count=Count("customer", distinct=True),
        )
        .order_by("-revenue")
    )
    revenue_by_plan = [
        {
            "plan": row["subscription__product__name"] or "Sem plano",
            "revenue": float(row["revenue"]),
            "customer_count": row["customer_count"],
        }
        for row in revenue_by_plan_qs
    ]

    # At-risk = suspended customers that have been suspended for more than 7 days
    seven_days_ago = now - datetime.timedelta(days=7)
    at_risk_count = Customer.objects.filter(
        deleted_at__isnull=True,
        status=Customer.Status.SUSPENDED,
        updated_at__lt=seven_days_ago,
    ).count()

    return {
        "mrr": mrr,
        "arr": mrr * 12,
        "active_customers": active_customers,
        "new_customers": new_customers,
        "churned_customers": churned_customers,
        "churn_rate": churn_rate,
        "at_risk_count": at_risk_count,
        "revenue_by_plan": revenue_by_plan,
        "monthly_revenue": [
            {"month": row["month"].strftime("%Y-%m"), "revenue": row["revenue"]}
            for row in monthly_revenue
        ],
    }
