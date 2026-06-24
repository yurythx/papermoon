from django.urls import path

from apps.cms.views import (
    RevalidateServicePageView,
    ServicePageAdminDetailView,
    ServicePageAdminListView,
    ServicePageGalleryDeleteView,
    ServicePageGalleryView,
    ServicePageHeroUploadView,
)

urlpatterns = [
    path("pages/", ServicePageAdminListView.as_view(), name="cms-admin-list"),
    path("pages/<slug:slug>/", ServicePageAdminDetailView.as_view(), name="cms-admin-detail"),
    path("pages/<slug:slug>/hero/", ServicePageHeroUploadView.as_view(), name="cms-admin-hero"),
    path("pages/<slug:slug>/gallery/", ServicePageGalleryView.as_view(), name="cms-admin-gallery"),
    path(
        "pages/<slug:slug>/gallery/<int:pk>/",
        ServicePageGalleryDeleteView.as_view(),
        name="cms-admin-gallery-delete",
    ),
    path("revalidate/<slug:slug>/", RevalidateServicePageView.as_view(), name="cms-revalidate"),
]
