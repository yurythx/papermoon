from django.urls import path

from apps.subscriptions.views_client import ClientLicenseDetailView, ClientLicenseListView

urlpatterns = [
    path("", ClientLicenseListView.as_view(), name="client-license-list"),
    path("<str:pk>/", ClientLicenseDetailView.as_view(), name="client-license-detail"),
]
