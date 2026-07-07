"""
Inbound REST adapter — views.

Each view's job, per spec: validate input -> call use case -> return
response. No business logic lives here; that belongs in the use cases
under application/use_cases/.

IMPORTANT ASSUMPTIONS (not yet confirmed against real code):
This project doesn't have all use case classes/adapters defined/shared
yet. To write working views, I assumed:

  - Each use case is a class with a single `execute(**kwargs)` method,
    constructed with the outbound adapters as dependencies, e.g.:

        RegisterUseCase(user_repository, token_service).execute(
            email=..., full_name=..., password=...
        ) -> tuple[TokenPair, User]

  - GoogleOAuthAdapter / GitHubOAuthAdapter exist at
    adapters/outbound/oauth/{google,github}_oauth_adapter.py, implementing
    OAuthProviderPort (confirmed: get_user_profile(code)), PLUS an
    additional get_authorization_url(state=None) -> str method needed for
    the two "initiate" redirect endpoints — that method wasn't shown in
    the OAuthProviderPort excerpt you shared, so confirm it's actually
    part of that port (or add it) before this compiles.

Adjust the imports/instantiation/argument names in the wiring section
below once the actual application/use_cases/*.py and
adapters/outbound/oauth/*.py files exist — the exception handling and
response-formatting logic won't need to change, only how each use case
is called.

KNOWN GAP: DRF's default behavior for `serializer.is_valid(raise_exception=True)`
returns validation errors as {"field": ["msg"]}, not the spec's
{status, error, message, timestamp} ErrorResponse envelope. That mismatch
needs a custom DRF exception handler (settings.py: REST_FRAMEWORK
EXCEPTION_HANDLER) — out of scope for this file, flagging so it isn't
missed.
"""
from datetime import datetime, timezone

from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from adapters.outbound.messaging.email_adapter import DjangoEmailService
from adapters.outbound.oauth.github_oauth_adapter import GitHubOAuthAdapter
from adapters.outbound.oauth.google_oauth_adapter import GoogleOAuthAdapter
from adapters.outbound.persistence.otp_repo import OTPRepository
from adapters.outbound.persistence.user_repo import UserRepository
from adapters.outbound.security.jwt_token_adapter import JWTTokenAdapter
from application.use_cases.activate_account import ActivateAccountUseCase
from application.use_cases.admin_reset_password import AdminResetPasswordUseCase
from application.use_cases.change_password import ChangePasswordUseCase
from application.use_cases.create_account import CreateAccountUseCase
from application.use_cases.deactivate_account import DeactivateAccountUseCase
from application.use_cases.forgot_password import ForgotPasswordUseCase
from application.use_cases.get_account import GetAccountUseCase
from application.use_cases.get_current_user import GetCurrentUserUseCase
from application.use_cases.login import LoginUseCase
from application.use_cases.logout import LogoutUseCase
from application.use_cases.oauth_login import OAuthLoginCommand, OAuthLoginUseCase
from application.use_cases.refresh_token import RefreshTokenUseCase
from application.use_cases.register import RegisterUseCase
from application.use_cases.reset_password import ResetPasswordUseCase
from application.use_cases.verify_otp import VerifyOtpUseCase
from domain.enums import OAuthProvider, UserRole
from domain.exceptions import (
    AccountInactiveError,
    EmailAlreadyExistsError,
    IncorrectPasswordError,
    InvalidCredentialsError,
    InvalidOtpError,
    InvalidTokenError,
    PasswordMismatchError,
    UserNotFoundError,
)

from .serializers import (
    AccountResponseSerializer,
    AuthResponseSerializer,
    ChangePasswordSerializer,
    CreateAccountSerializer,
    CurrentUserResponseSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    OAuthCallbackSerializer,
    OtpVerifiedResponseSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    VerifyOtpSerializer,
)

# ---------------------------------------------------------------------
# Wiring — construct outbound adapters once, then the use cases that
# depend on them. See module docstring: use case constructor signatures
# here are assumed, not confirmed.
# ---------------------------------------------------------------------

_user_repository = UserRepository()
_otp_service = OTPRepository()
_token_service = JWTTokenAdapter()
_email_service = DjangoEmailService()
_google_oauth_adapter = GoogleOAuthAdapter()
_github_oauth_adapter = GitHubOAuthAdapter()

_register_use_case = RegisterUseCase(_user_repository, _token_service)
_login_use_case = LoginUseCase(_user_repository, _token_service)
_refresh_token_use_case = RefreshTokenUseCase(_token_service, _user_repository)
_logout_use_case = LogoutUseCase(_token_service)
_get_current_user_use_case = GetCurrentUserUseCase(_user_repository)
_forgot_password_use_case = ForgotPasswordUseCase(
    _user_repository, _otp_service, _email_service
)
_verify_otp_use_case = VerifyOtpUseCase(_otp_service, _user_repository, _token_service)
_reset_password_use_case = ResetPasswordUseCase(_token_service, _user_repository)
_change_password_use_case = ChangePasswordUseCase(_user_repository, _token_service)
_create_account_use_case = CreateAccountUseCase(_user_repository, _email_service)
_get_account_use_case = GetAccountUseCase(_user_repository)
_activate_account_use_case = ActivateAccountUseCase(_user_repository)
_deactivate_account_use_case = DeactivateAccountUseCase(_user_repository, _token_service)
_admin_reset_password_use_case = AdminResetPasswordUseCase(
    _user_repository, _token_service, _email_service
)
_google_oauth_login_use_case = OAuthLoginUseCase(
    _user_repository, _token_service, _google_oauth_adapter
)
_github_oauth_login_use_case = OAuthLoginUseCase(
    _user_repository, _token_service, _github_oauth_adapter
)

# ---------------------------------------------------------------------
# Domain exception -> HTTP status/code mapping (exact table from spec)
# ---------------------------------------------------------------------

EXCEPTION_STATUS_MAP = {
    EmailAlreadyExistsError: (status.HTTP_409_CONFLICT, "CONFLICT"),
    InvalidCredentialsError: (status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED"),
    AccountInactiveError: (status.HTTP_403_FORBIDDEN, "FORBIDDEN"),
    InvalidTokenError: (status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED"),
    InvalidOtpError: (status.HTTP_400_BAD_REQUEST, "BAD_REQUEST"),
    IncorrectPasswordError: (status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED"),
    UserNotFoundError: (status.HTTP_404_NOT_FOUND, "NOT_FOUND"),
    PasswordMismatchError: (status.HTTP_400_BAD_REQUEST, "BAD_REQUEST"),
}


def _error_body(status_code: int, error_code: str, message: str) -> dict:
    return {
        "status": status_code,
        "error": error_code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class BaseAuthView(APIView):
    """
    Shared plumbing only — domain-exception -> HTTP mapping, bearer-token
    extraction, and admin-role gating. No endpoint-specific business logic.
    """

    def handle_domain_exception(self, exc: Exception) -> Response:
        for exc_type, (status_code, error_code) in EXCEPTION_STATUS_MAP.items():
            if isinstance(exc, exc_type):
                return Response(
                    _error_body(status_code, error_code, str(exc)),
                    status=status_code,
                )
        # Not a recognized domain exception — re-raise so DRF's default
        # exception handling (and logging) takes over rather than us
        # silently returning a wrong status code.
        raise exc

    @staticmethod
    def _bearer_token(request) -> str | None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        return auth_header[len("Bearer "):]

    def authenticate(self, request):
        """Returns a TokenPayload, or raises InvalidTokenError."""
        token = self._bearer_token(request)
        if token is None:
            raise InvalidTokenError("Authentication token is missing or invalid.")
        return _token_service.validate_access_token(token)

    @staticmethod
    def require_admin(payload) -> Response | None:
        """Returns a 403 Response if the caller isn't an admin, else None."""
        if payload.role != UserRole.ADMIN:
            return Response(
                _error_body(
                    status.HTTP_403_FORBIDDEN,
                    "FORBIDDEN",
                    "You do not have permission to perform this action.",
                ),
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @staticmethod
    def auth_response_data(tokens, user) -> dict:
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in,
            "user": user,
        }


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------

class RegisterView(BaseAuthView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            tokens, user = _register_use_case.execute(
                email=data["email"],
                full_name=data["fullName"],
                password=data["password"],
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            AuthResponseSerializer(self.auth_response_data(tokens, user)).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(BaseAuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            tokens, user = _login_use_case.execute(
                email=data["email"], password=data["password"]
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AuthResponseSerializer(self.auth_response_data(tokens, user)).data)


class RefreshTokenView(BaseAuthView):
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tokens, user = _refresh_token_use_case.execute(
                refresh_token=serializer.validated_data["refreshToken"]
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AuthResponseSerializer(self.auth_response_data(tokens, user)).data)


class LogoutView(BaseAuthView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.authenticate(request)
            _logout_use_case.execute(
                refresh_token=serializer.validated_data["refreshToken"]
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(BaseAuthView):
    def get(self, request):
        try:
            payload = self.authenticate(request)
            user = _get_current_user_use_case.execute(user_id=payload.user_id)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(CurrentUserResponseSerializer(user).data)


# ---------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------

class ForgotPasswordView(BaseAuthView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            _forgot_password_use_case.execute(
                email=serializer.validated_data["email"]
            )
        except UserNotFoundError:
            # Deliberately swallowed: always return 200 regardless of
            # whether the email is registered, to avoid user enumeration
            # (per spec).
            pass
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            {"message": "If an account with that email exists, a reset code has been sent."}
        )


class VerifyOtpView(BaseAuthView):
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            reset_token, expires_in = _verify_otp_use_case.execute(
                email=data["email"], otp=data["otp"]
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            OtpVerifiedResponseSerializer(
                {"reset_token": reset_token, "expires_in": expires_in}
            ).data
        )


class ResetPasswordView(BaseAuthView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            _reset_password_use_case.execute(
                reset_token=data["resetToken"], new_password=data["newPassword"]
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            {"message": "Password has been reset successfully. Please log in again."}
        )


class ChangePasswordView(BaseAuthView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payload = self.authenticate(request)
            _change_password_use_case.execute(
                user_id=payload.user_id,
                current_password=data["currentPassword"],
                new_password=data["newPassword"],
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            {"message": "Password changed successfully. Please log in again."}
        )


# ---------------------------------------------------------------------
# Admin account management
# ---------------------------------------------------------------------

class CreateAccountView(BaseAuthView):
    def post(self, request):
        serializer = CreateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            account = _create_account_use_case.execute(
                email=data["email"], full_name=data["fullName"], role=data["role"]
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            AccountResponseSerializer(account).data, status=status.HTTP_201_CREATED
        )


class GetAccountView(BaseAuthView):
    def get(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            account = _get_account_use_case.execute(user_id=user_id)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AccountResponseSerializer(account).data)


class ActivateAccountView(BaseAuthView):
    def post(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            account = _activate_account_use_case.execute(user_id=user_id)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AccountResponseSerializer(account).data)


class DeactivateAccountView(BaseAuthView):
    def post(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            account = _deactivate_account_use_case.execute(user_id=user_id)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AccountResponseSerializer(account).data)


class AdminResetPasswordView(BaseAuthView):
    def post(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            _admin_reset_password_use_case.execute(user_id=user_id)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            {"message": "A temporary password has been sent to the user's email."}
        )


# ---------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------

class GoogleOAuthInitiateView(BaseAuthView):
    """GET /auth/oauth/google — redirects to Google's authorization page."""

    def get(self, request):
        state = request.query_params.get("state")
        authorization_url = _google_oauth_adapter.get_authorization_url(state=state)
        return HttpResponseRedirect(authorization_url)


class GoogleOAuthCallbackView(BaseAuthView):
    """GET /auth/oauth/google/callback"""

    def get(self, request):
        serializer = OAuthCallbackSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            result = _google_oauth_login_use_case.execute(
                OAuthLoginCommand(
                    authorization_code=serializer.validated_data["code"],
                    provider=OAuthProvider.GOOGLE,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            AuthResponseSerializer(
                self.auth_response_data(result, result.user)
            ).data
        )


class GitHubOAuthInitiateView(BaseAuthView):
    """GET /auth/oauth/github — redirects to GitHub's authorization page."""

    def get(self, request):
        state = request.query_params.get("state")
        authorization_url = _github_oauth_adapter.get_authorization_url(state=state)
        return HttpResponseRedirect(authorization_url)


class GitHubOAuthCallbackView(BaseAuthView):
    """GET /auth/oauth/github/callback"""

    def get(self, request):
        serializer = OAuthCallbackSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            result = _github_oauth_login_use_case.execute(
                OAuthLoginCommand(
                    authorization_code=serializer.validated_data["code"],
                    provider=OAuthProvider.GITHUB,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            AuthResponseSerializer(
                self.auth_response_data(result, result.user)
            ).data
        )