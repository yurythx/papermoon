from django.urls import path

from shared.views import ContactView, HealthCheckView

urlpatterns = [
    path("", HealthCheckView.as_view(), name="health"),
]

contact_urlpatterns = [
    path("contact/", ContactView.as_view(), name="contact"),
]
