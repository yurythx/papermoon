from django.urls import path

from apps.subscriptions.views_admin import (
    AdminSubscriptionCancelView,
    AdminSubscriptionChangePlanView,
    AdminSubscriptionDetailView,
    AdminSubscriptionListCreateView,
    AdminSubscriptionRenewView,
    AdminSubscriptionSuspendView,
)
from apps.subscriptions.views_service_access import (
    AdminServiceAccessDetailView,
    AdminServiceAccessListCreateView,
    AdminServiceAccessReprovisionView,
)

urlpatterns = [
    # Subscriptions
    path(
        "subscriptions/", AdminSubscriptionListCreateView.as_view(), name="admin-subscription-list"
    ),
    path(
        "subscriptions/<str:pk>/",
        AdminSubscriptionDetailView.as_view(),
        name="admin-subscription-detail",
    ),
    path(
        "subscriptions/<str:pk>/suspend/",
        AdminSubscriptionSuspendView.as_view(),
        name="admin-subscription-suspend",
    ),
    path(
        "subscriptions/<str:pk>/renew/",
        AdminSubscriptionRenewView.as_view(),
        name="admin-subscription-renew",
    ),
    path(
        "subscriptions/<str:pk>/cancel/",
        AdminSubscriptionCancelView.as_view(),
        name="admin-subscription-cancel",
    ),
    path(
        "subscriptions/<str:pk>/change-plan/",
        AdminSubscriptionChangePlanView.as_view(),
        name="admin-subscription-change-plan",
    ),
    # ServiceAccess por assinatura
    path(
        "subscriptions/<str:subscription_pk>/services/",
        AdminServiceAccessListCreateView.as_view(),
        name="admin-service-access-list",
    ),
    # ServiceAccess individual
    path(
        "service-accesses/<str:pk>/",
        AdminServiceAccessDetailView.as_view(),
        name="admin-service-access-detail",
    ),
    path(
        "service-accesses/<str:pk>/reprovision/",
        AdminServiceAccessReprovisionView.as_view(),
        name="admin-service-access-reprovision",
    ),
]
