from django.urls import path

from apps.subscriptions.views_client import (
    ClientChangePlanPreviewView,
    ClientLicenseValidateView,
    ClientSubscriptionCancelView,
    ClientSubscriptionChangePlanView,
    ClientSubscriptionDetailView,
    ClientSubscriptionListView,
    ClientSubscriptionReactivateView,
)
from apps.subscriptions.views_service_access import ClientServiceAccessListView

urlpatterns = [
    path("", ClientSubscriptionListView.as_view(), name="client-subscription-list"),
    path("validate-license/", ClientLicenseValidateView.as_view(), name="validate-license"),
    path("<str:pk>/", ClientSubscriptionDetailView.as_view(), name="client-subscription-detail"),
    path(
        "<str:subscription_pk>/services/",
        ClientServiceAccessListView.as_view(),
        name="client-service-access-list",
    ),
    path(
        "<str:pk>/change-plan-preview/",
        ClientChangePlanPreviewView.as_view(),
        name="client-subscription-change-plan-preview",
    ),
    path(
        "<str:pk>/change-plan/",
        ClientSubscriptionChangePlanView.as_view(),
        name="client-subscription-change-plan",
    ),
    path(
        "<str:pk>/reactivate/",
        ClientSubscriptionReactivateView.as_view(),
        name="client-subscription-reactivate",
    ),
    path(
        "<str:pk>/cancel/",
        ClientSubscriptionCancelView.as_view(),
        name="client-subscription-cancel",
    ),
]
