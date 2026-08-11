from django.urls import path

from apps.subscriptions.views_client import (
    ClientChangePlanPreviewView,
    ClientKeycloakIntegrationGuideView,
    ClientKeycloakIntegrationListCreateView,
    ClientKeycloakIntegrationSecretView,
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
    # Registrados ANTES de <str:pk>/ (mesma razão de validate-license/ acima):
    # sem isso, o path genérico de pk engoliria esses segmentos fixos como se
    # fossem um valor de pk.
    path(
        "keycloak-integration-guide/",
        ClientKeycloakIntegrationGuideView.as_view(),
        name="client-keycloak-integration-guide",
    ),
    path(
        "keycloak-integrations/",
        ClientKeycloakIntegrationListCreateView.as_view(),
        name="client-keycloak-integrations",
    ),
    path(
        "keycloak-integrations/<uuid:pk>/secret/",
        ClientKeycloakIntegrationSecretView.as_view(),
        name="client-keycloak-integration-secret",
    ),
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
