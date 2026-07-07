"""
Maps URL paths to view classes. Matches the OpenAPI spec paths (all
under the api/v1/ prefix added in config/urls.py).

The 14-path table given in the task doesn't include the 4 OAuth paths
(/auth/oauth/google[...], /auth/oauth/github[...]) — those come from the
OpenAPI spec itself and the OAuth views already built, so I've included
them too, clearly separated below.
"""
from django.urls import path

from .views import (
    ActivateAccountView,
    AdminResetPasswordView,
    ChangePasswordView,
    CreateAccountView,
    CurrentUserView,
    DeactivateAccountView,
    ForgotPasswordView,
    GetAccountView,
    GitHubOAuthCallbackView,
    GitHubOAuthInitiateView,
    GoogleOAuthCallbackView,
    GoogleOAuthInitiateView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    RegisterView,
    ResetPasswordView,
    VerifyOtpView,
)

urlpatterns = [
    # -- Authentication --
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="refresh-token"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),

    # -- Password reset --
    path("auth/password/forgot/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("auth/password/verify-otp/", VerifyOtpView.as_view(), name="verify-otp"),
    path("auth/password/reset/", ResetPasswordView.as_view(), name="reset-password"),
    path("auth/password/change/", ChangePasswordView.as_view(), name="change-password"),

    # -- Admin account management --
    path("auth/admin/accounts/", CreateAccountView.as_view(), name="create-account"),
    path(
        "auth/admin/accounts/<uuid:user_id>/",
        GetAccountView.as_view(),
        name="get-account",
    ),
    path(
        "auth/admin/accounts/<uuid:user_id>/activate/",
        ActivateAccountView.as_view(),
        name="activate-account",
    ),
    path(
        "auth/admin/accounts/<uuid:user_id>/deactivate/",
        DeactivateAccountView.as_view(),
        name="deactivate-account",
    ),
    path(
        "auth/admin/accounts/<uuid:user_id>/reset-password/",
        AdminResetPasswordView.as_view(),
        name="admin-reset-password",
    ),

    # -- OAuth (from the OpenAPI spec, not in the 14-path table above) --
    path(
        "auth/oauth/google/",
        GoogleOAuthInitiateView.as_view(),
        name="google-oauth-initiate",
    ),
    path(
        "auth/oauth/google/callback/",
        GoogleOAuthCallbackView.as_view(),
        name="google-oauth-callback",
    ),
    path(
        "auth/oauth/github/",
        GitHubOAuthInitiateView.as_view(),
        name="github-oauth-initiate",
    ),
    path(
        "auth/oauth/github/callback/",
        GitHubOAuthCallbackView.as_view(),
        name="github-oauth-callback",
    ),
]