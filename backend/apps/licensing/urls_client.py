from django.urls import path

from apps.licensing.views import ApiKeyListCreateView, ApiKeyRevokeView, DailyApiUsageView

urlpatterns = [
    path("", ApiKeyListCreateView.as_view(), name="client-api-key-list"),
    path("usage/daily/", DailyApiUsageView.as_view(), name="client-api-usage-daily"),
    path("<str:pk>/", ApiKeyRevokeView.as_view(), name="client-api-key-revoke"),
]
