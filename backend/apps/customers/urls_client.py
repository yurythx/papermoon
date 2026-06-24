from django.urls import path

from apps.customers.views_client import (
    ClientApiQuotaView,
    ClientFinancialMetricsView,
    ClientInvoiceExportView,
    ClientInvoiceListView,
    CustomerMeView,
    InvitationListCreateView,
    InvitationResendView,
    InvitationRevokeView,
    TeamMemberDetailView,
    TeamMembersView,
)

urlpatterns = [
    # Profile & tenant
    path("me/", CustomerMeView.as_view(), name="client-me"),
    # Billing
    path("invoices/", ClientInvoiceListView.as_view(), name="client-invoices"),
    path("invoices/export/", ClientInvoiceExportView.as_view(), name="client-invoices-export"),
    path("metrics/", ClientFinancialMetricsView.as_view(), name="client-metrics"),
    # Licensing
    path("quota/", ClientApiQuotaView.as_view(), name="client-quota"),
    # Team
    path("team/", TeamMembersView.as_view(), name="client-team"),
    path("team/<str:pk>/", TeamMemberDetailView.as_view(), name="client-team-detail"),
    # Team invitations
    path("invitations/", InvitationListCreateView.as_view(), name="client-invitation-list"),
    path("invitations/<str:pk>/", InvitationRevokeView.as_view(), name="client-invitation-revoke"),
    path(
        "invitations/<str:pk>/resend/",
        InvitationResendView.as_view(),
        name="client-invitation-resend",
    ),
]
