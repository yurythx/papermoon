from django.urls import path

from apps.billing.views import (
    AdminAPIUsageMetricsView,
    AdminInvoiceListView,
    AdminInvoiceSoftDeleteView,
    AdminMRRMetricsView,
)

urlpatterns = [
    path("metrics/mrr/", AdminMRRMetricsView.as_view(), name="billing-metrics-mrr"),
    path(
        "metrics/api-usage/", AdminAPIUsageMetricsView.as_view(), name="billing-metrics-api-usage"
    ),
    path("invoices/", AdminInvoiceListView.as_view(), name="admin-invoice-list"),
    path(
        "invoices/<str:pk>/", AdminInvoiceSoftDeleteView.as_view(), name="admin-invoice-soft-delete"
    ),
]
