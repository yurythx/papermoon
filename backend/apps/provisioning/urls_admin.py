from django.urls import path

from apps.provisioning.views_admin import KeycloakConnectionAdminView, KeycloakConnectionTestView

urlpatterns = [
    path(
        "keycloak-connection/",
        KeycloakConnectionAdminView.as_view(),
        name="admin-keycloak-connection",
    ),
    path(
        "keycloak-connection/test/",
        KeycloakConnectionTestView.as_view(),
        name="admin-keycloak-connection-test",
    ),
]
