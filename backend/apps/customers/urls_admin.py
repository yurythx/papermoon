from django.urls import path

from apps.customers.views_admin import (
    AdminMetricsView,
    CustomerCancelView,
    CustomerDetailView,
    CustomerListCreateView,
    CustomerQuotaView,
    CustomerReactivateView,
    CustomerSoftDeleteView,
    CustomerSuspendView,
)

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="admin-customer-list"),
    path("customers/<str:pk>/", CustomerDetailView.as_view(), name="admin-customer-detail"),
    path(
        "customers/<str:pk>/suspend/", CustomerSuspendView.as_view(), name="admin-customer-suspend"
    ),
    path(
        "customers/<str:pk>/reactivate/",
        CustomerReactivateView.as_view(),
        name="admin-customer-reactivate",
    ),
    path("customers/<str:pk>/cancel/", CustomerCancelView.as_view(), name="admin-customer-cancel"),
    path(
        "customers/<str:pk>/delete/",
        CustomerSoftDeleteView.as_view(),
        name="admin-customer-soft-delete",
    ),
    path("customers/<str:pk>/quota/", CustomerQuotaView.as_view(), name="admin-customer-quota"),
    path("metrics/", AdminMetricsView.as_view(), name="admin-metrics"),
]
