from django.urls import path

from apps.cms.views import ServicePageDetailView, ServiceSlugListView

urlpatterns = [
    path("services/", ServiceSlugListView.as_view(), name="cms-service-list"),
    path("services/<slug:slug>/", ServicePageDetailView.as_view(), name="cms-service-detail"),
]
