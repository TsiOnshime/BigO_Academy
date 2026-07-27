"""
Re-exports every view so urls.py can do:
    from adapters.inbound.rest.views import RegisterView, LoginView, ...
without needing to know which submodule each view lives in.
"""
from .admin_views import (
    ActivateAccountView,
    AdminResetPasswordView,
    CreateAccountView,
    DeactivateAccountView,
    GetAccountView,
)
from .auth_views import CurrentUserView, LoginView, LogoutView, RefreshTokenView, RegisterView
from .oauth_views import (
    GitHubOAuthCallbackView,
    GitHubOAuthInitiateView,
    GoogleOAuthCallbackView,
    GoogleOAuthInitiateView,
)
from .password_views import (
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
    VerifyOtpView,
)

__all__ = [
    "RegisterView",
    "LoginView",
    "RefreshTokenView",
    "LogoutView",
    "CurrentUserView",
    "ForgotPasswordView",
    "VerifyOtpView",
    "ResetPasswordView",
    "ChangePasswordView",
    "CreateAccountView",
    "GetAccountView",
    "ActivateAccountView",
    "DeactivateAccountView",
    "AdminResetPasswordView",
    "GoogleOAuthInitiateView",
    "GoogleOAuthCallbackView",
    "GitHubOAuthInitiateView",
    "GitHubOAuthCallbackView",
]