from django.urls import path

from apps.flags.views_admin import FeatureFlagDetailView, FeatureFlagListCreateView

urlpatterns = [
    path("feature-flags/", FeatureFlagListCreateView.as_view(), name="feature-flag-list"),
    path("feature-flags/<int:pk>/", FeatureFlagDetailView.as_view(), name="feature-flag-detail"),
]
