"""
infrastructure/config/dependencies.py

The ONLY place in the codebase where concrete adapter classes are
imported and combined with use cases. Everywhere else (use cases, views)
only knows about abstract port interfaces.

NAMING MISMATCH — flagging rather than silently fixing:
The task's example pattern names adapters DjangoUserRepository /
JWTTokenService / DjangoOtpService. The classes that actually exist in
this project are:
    UserRepository       (your own authored file — kept as-is)
    JWTTokenAdapter       (built by me earlier)
    OTPRepository         (built by me earlier)
    DjangoEmailService    (built by me earlier — this one already matches)

If you want strict naming-convention consistency with the course
pattern, I can rename JWTTokenAdapter -> JWTTokenService and
OTPRepository -> DjangoOtpService (both mine, safe to rename). I did NOT
rename UserRepository since that's your own file — let me know if you
want that renamed to DjangoUserRepository too.

Two factories below (get_token_service, get_google/github_oauth_adapter)
aren't "use case" factories — they hand back a bare adapter instance.
They exist because BaseAuthView.authenticate() and the OAuth initiate
views need direct adapter access that isn't wrapped in a use case.
"""
from adapters.outbound.messaging.email_adapter import DjangoEmailService
from adapters.outbound.oauth.github_oauth_adapter import GitHubOAuthAdapter
from adapters.outbound.oauth.google_oauth_adapter import GoogleOAuthAdapter
from adapters.outbound.persistence.otp_repo import OTPRepository
from adapters.outbound.persistence.user_repo import UserRepository
from adapters.outbound.security.jwt_token_adapter import JWTTokenAdapter
from adapters.outbound.security.password_hasher_adapter import PasswordHasherAdapter
from application.ports.outbound.oauth_provider import OAuthProviderPort
from application.ports.outbound.token_service import TokenServicePort
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
from application.use_cases.oauth_login import OAuthLoginUseCase
from application.use_cases.refresh_token import RefreshTokenUseCase
from application.use_cases.register_student import RegisterStudentUseCase
from application.use_cases.reset_password import ResetPasswordUseCase
from application.use_cases.verify_otp import VerifyOtpUseCase

# ---------------------------------------------------------------------
# Bare adapter access (not use cases, but needed directly by views)
# ---------------------------------------------------------------------

def get_token_service() -> TokenServicePort:
    return JWTTokenAdapter()


def get_google_oauth_adapter() -> OAuthProviderPort:
    return GoogleOAuthAdapter()


def get_github_oauth_adapter() -> OAuthProviderPort:
    return GitHubOAuthAdapter()


# ---------------------------------------------------------------------
# Use case factories
# CONFIRMED shape (built from real files shared): register_student,
# create_account, oauth_login.
# GUESSED shape (extrapolated pattern — adjust once real files exist):
# everything else.
# ---------------------------------------------------------------------

def get_register_use_case() -> RegisterStudentUseCase:
    return RegisterStudentUseCase(
        user_repository=UserRepository(),
        token_service=JWTTokenAdapter(),
        password_hasher=PasswordHasherAdapter(),
    )


def get_login_use_case() -> LoginUseCase:
    return LoginUseCase(
        user_repository=UserRepository(),
        password_hasher=PasswordHasherAdapter(),
        token_service=JWTTokenAdapter(),
    )


def get_refresh_token_use_case() -> RefreshTokenUseCase:
    return RefreshTokenUseCase(
        token_service=JWTTokenAdapter(),
        user_repository=UserRepository(),
    )


def get_logout_use_case() -> LogoutUseCase:
    return LogoutUseCase(token_service=JWTTokenAdapter())


def get_current_user_use_case() -> GetCurrentUserUseCase:
    return GetCurrentUserUseCase(user_repository=UserRepository())


def get_forgot_password_use_case() -> ForgotPasswordUseCase:
    return ForgotPasswordUseCase(
        user_repository=UserRepository(),
        otp_service=OTPRepository(),
        email_service=DjangoEmailService(),
    )


def get_verify_otp_use_case() -> VerifyOtpUseCase:
    return VerifyOtpUseCase(
        otp_service=OTPRepository(),
        user_repository=UserRepository(),
        token_service=JWTTokenAdapter(),
    )


def get_reset_password_use_case() -> ResetPasswordUseCase:
    return ResetPasswordUseCase(
        token_service=JWTTokenAdapter(),
        user_repository=UserRepository(),
        password_hasher=PasswordHasherAdapter(),
    )


def get_change_password_use_case() -> ChangePasswordUseCase:
    return ChangePasswordUseCase(
        user_repository=UserRepository(),
        password_hasher=PasswordHasherAdapter(),
        token_service=JWTTokenAdapter(),
    )


def get_create_account_use_case() -> CreateAccountUseCase:
    return CreateAccountUseCase(
        user_repository=UserRepository(),
        password_hasher=PasswordHasherAdapter(),
        email_service=DjangoEmailService(),
    )


def get_account_use_case() -> GetAccountUseCase:
    return GetAccountUseCase(user_repository=UserRepository())


def get_activate_account_use_case() -> ActivateAccountUseCase:
    return ActivateAccountUseCase(user_repository=UserRepository())


def get_deactivate_account_use_case() -> DeactivateAccountUseCase:
    return DeactivateAccountUseCase(
        user_repository=UserRepository(),
        token_service=JWTTokenAdapter(),
    )


def get_admin_reset_password_use_case() -> AdminResetPasswordUseCase:
    return AdminResetPasswordUseCase(
        user_repository=UserRepository(),
        password_hasher=PasswordHasherAdapter(),
        email_service=DjangoEmailService(),
    )


def get_google_oauth_login_use_case() -> OAuthLoginUseCase:
    return OAuthLoginUseCase(
        user_repository=UserRepository(),
        token_service=JWTTokenAdapter(),
        oauth_provider=GoogleOAuthAdapter(),
    )


def get_github_oauth_login_use_case() -> OAuthLoginUseCase:
    return OAuthLoginUseCase(
        user_repository=UserRepository(),
        token_service=JWTTokenAdapter(),
        oauth_provider=GitHubOAuthAdapter(),
    )