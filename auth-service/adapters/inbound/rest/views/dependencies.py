"""
Composition root for the inbound REST layer: instantiate every outbound
adapter once, then every use case that depends on them.

IMPORTANT — READ BEFORE EDITING:
Two use cases are built from files you've actually shared, so their
Command/Result shape is confirmed:
    - CreateAccountUseCase  (CreateAccountCommand -> CreateAccountResult)
    - OAuthLoginUseCase     (OAuthLoginCommand -> OAuthLoginResult)

Every OTHER use case imported below is a GUESS, extrapolated from that
same Command-in/Result-out pattern. The class names, constructor argument
order, and Command/Result field names are NOT confirmed. Treat each
import + wiring line as a placeholder to correct once the real
application/use_cases/*.py files exist.

Also new since the CreateAccountUseCase reveal: a PasswordHasherPort is
required (for hashing passwords on register/create-account and verifying
them on login/change-password) and hasn't been built as an adapter yet.
_password_hasher below points at an adapter that doesn't exist yet —
build adapters/outbound/security/password_hasher_adapter.py next.
"""
from adapters.outbound.messaging.email_adapter import DjangoEmailService
from adapters.outbound.oauth.github_oauth_adapter import GitHubOAuthAdapter
from adapters.outbound.oauth.google_oauth_adapter import GoogleOAuthAdapter
from adapters.outbound.persistence.otp_repo import OTPRepository
from adapters.outbound.persistence.user_repo import UserRepository
from adapters.outbound.security.jwt_token_adapter import JWTTokenAdapter

# NOT YET BUILT — see module docstring.
from adapters.outbound.security.password_hasher_adapter import PasswordHasherAdapter

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
from application.use_cases.register_student import RegisterUseCase
from application.use_cases.reset_password import ResetPasswordUseCase
from application.use_cases.verify_otp import VerifyOtpUseCase

# ---------------------------------------------------------------------
# Outbound adapters (singletons)
# ---------------------------------------------------------------------

user_repository = UserRepository()
otp_service = OTPRepository()
token_service = JWTTokenAdapter()
email_service = DjangoEmailService()
password_hasher = PasswordHasherAdapter()  # NOT YET BUILT
google_oauth_adapter = GoogleOAuthAdapter()
github_oauth_adapter = GitHubOAuthAdapter()

# ---------------------------------------------------------------------
# Use cases (singletons)
# ---------------------------------------------------------------------

# -- CONFIRMED shape (built from real files you shared) --
create_account_use_case = CreateAccountUseCase(
    user_repository, password_hasher, email_service
)
google_oauth_login_use_case = OAuthLoginUseCase(
    user_repository, token_service, google_oauth_adapter
)
github_oauth_login_use_case = OAuthLoginUseCase(
    user_repository, token_service, github_oauth_adapter
)

# -- GUESSED shape (adjust once real files exist) --
register_use_case = RegisterUseCase(user_repository, password_hasher, token_service)
login_use_case = LoginUseCase(user_repository, password_hasher, token_service)
refresh_token_use_case = RefreshTokenUseCase(token_service, user_repository)
logout_use_case = LogoutUseCase(token_service)
get_current_user_use_case = GetCurrentUserUseCase(user_repository)
forgot_password_use_case = ForgotPasswordUseCase(user_repository, otp_service, email_service)
verify_otp_use_case = VerifyOtpUseCase(otp_service, user_repository, token_service)
reset_password_use_case = ResetPasswordUseCase(token_service, user_repository, password_hasher)
change_password_use_case = ChangePasswordUseCase(user_repository, password_hasher, token_service)
get_account_use_case = GetAccountUseCase(user_repository)
activate_account_use_case = ActivateAccountUseCase(user_repository)
deactivate_account_use_case = DeactivateAccountUseCase(user_repository, token_service)
admin_reset_password_use_case = AdminResetPasswordUseCase(
    user_repository, password_hasher, email_service
)