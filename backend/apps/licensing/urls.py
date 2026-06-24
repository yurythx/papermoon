from django.urls import path

from apps.licensing.views import ValidateKeyView

urlpatterns = [
    path("validate-key/", ValidateKeyView.as_view(), name="validate-key"),
]
