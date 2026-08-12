from django.urls import path

from apps.blog.views_admin import (
    BlogPostAdminDetailView,
    BlogPostAdminListCreateView,
    BlogPostBodyImageUploadView,
    BlogPostCoverUploadView,
)

urlpatterns = [
    path("", BlogPostAdminListCreateView.as_view(), name="blog-admin-list"),
    path("<uuid:pk>/", BlogPostAdminDetailView.as_view(), name="blog-admin-detail"),
    path("<uuid:pk>/cover/", BlogPostCoverUploadView.as_view(), name="blog-admin-cover"),
    path(
        "<uuid:pk>/body-image/", BlogPostBodyImageUploadView.as_view(), name="blog-admin-body-image"
    ),
]
