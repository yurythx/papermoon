from django.urls import path

from apps.billing.views import AsaasWebhookView

urlpatterns = [
    path("asaas/", AsaasWebhookView.as_view(), name="webhook-asaas"),
]
