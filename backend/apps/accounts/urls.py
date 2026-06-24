from django.urls import path

from apps.accounts.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PendingRegistrationsView,
    ProvisionUserView,
    RefreshTokenView,
    RegisterView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("register/", RegisterView.as_view(), name="auth-register"),
    path(
        "pending-registrations/",
        PendingRegistrationsView.as_view(),
        name="auth-pending-registrations",
    ),
    path(
        "pending-registrations/<str:user_id>/provision/",
        ProvisionUserView.as_view(),
        name="auth-provision-user",
    ),
]
