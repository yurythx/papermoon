from django.urls import path

from apps.customers.views_invitations import AcceptInvitationView

urlpatterns = [
    path("accept/", AcceptInvitationView.as_view(), name="invitation-accept"),
]
