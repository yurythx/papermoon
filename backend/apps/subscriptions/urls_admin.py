from django.urls import path

from apps.subscriptions.views_admin import (
    AdminKeycloakCodeSnippetView,
    AdminKeycloakIntegrationGuideView,
    AdminKeycloakIntegrationListCreateView,
    AdminKeycloakIntegrationSecretView,
    AdminKeycloakIssuerValidatorView,
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
    # Keycloak — ferramentas de suporte (staff agindo em nome de um cliente,
    # + validador genérico sem vínculo com cliente nenhum)
    path(
        "keycloak-tools/validate-issuer/",
        AdminKeycloakIssuerValidatorView.as_view(),
        name="admin-keycloak-validate-issuer",
    ),
    path(
        "keycloak-tools/render-snippet/",
        AdminKeycloakCodeSnippetView.as_view(),
        name="admin-keycloak-render-snippet",
    ),
    path(
        "customers/<uuid:customer_id>/keycloak-integration-guide/",
        AdminKeycloakIntegrationGuideView.as_view(),
        name="admin-keycloak-integration-guide",
    ),
    path(
        "customers/<uuid:customer_id>/keycloak-integrations/",
        AdminKeycloakIntegrationListCreateView.as_view(),
        name="admin-keycloak-integrations",
    ),
    path(
        "customers/<uuid:customer_id>/keycloak-integrations/<uuid:pk>/secret/",
        AdminKeycloakIntegrationSecretView.as_view(),
        name="admin-keycloak-integration-secret",
    ),
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
