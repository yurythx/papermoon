from django.urls import path

from apps.accounts.views import SSOConfigAdminView, SSOConfigTestView

urlpatterns = [
    path("sso-config/", SSOConfigAdminView.as_view(), name="admin-sso-config"),
    path("sso-config/test/", SSOConfigTestView.as_view(), name="admin-sso-config-test"),
]
