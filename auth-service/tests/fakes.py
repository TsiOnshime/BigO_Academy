from uuid import UUID
from domain.models import User
from domain.enums import OAuthProvider
from domain.exceptions import InvalidTokenError
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort, TokenPair, TokenPayload
from application.ports.outbound.password_hasher import PasswordHasherPort
from application.ports.outbound.otp_service import OtpServicePort
from application.ports.outbound.email_service import EmailServicePort
from application.ports.outbound.oauth_provider import OAuthProviderPort, OAuthUserProfile


class FakeUserRepository(UserRepositoryPort):
    """
    Stores users in a plain Python dictionary.
    No database involved — purely for testing.
    """

    def __init__(self):
        self._store: dict[UUID, User] = {}

    def save(self, user: User) -> User:
        self._store[user.id] = user
        return user

    def find_by_email(self, email: str) -> User | None:
        for user in self._store.values():
            if user.email == email:
                return user
        return None

    def find_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(user_id)

    def email_exists(self, email: str) -> bool:
        return self.find_by_email(email) is not None


class FakeTokenService(TokenServicePort):
    """
    Returns predictable fake tokens for testing.
    Tracks which tokens have been revoked.
    """

    def __init__(self):
        self._revoked: set[str] = set()
        self._revoked_users: set[UUID] = set()

    def generate_tokens(self, user) -> TokenPair:
        return TokenPair(
            access_token=f"fake_access_{user.id}",
            refresh_token=f"fake_refresh_{user.id}",
        )

    def validate_access_token(self, token: str) -> TokenPayload:
        if token in self._revoked:
            raise InvalidTokenError()
        # Extract user_id from our fake token format
        user_id = UUID(token.replace("fake_access_", ""))
        return TokenPayload(
            user_id=user_id,
            email="test@example.com",
            role="STUDENT",
        )

    def validate_refresh_token(self, token: str) -> TokenPayload:
        if token in self._revoked:
            raise InvalidTokenError("Token has been revoked")
        user_id = UUID(token.replace("fake_refresh_", ""))
        if user_id in self._revoked_users:
            raise InvalidTokenError("All tokens revoked for this user")
        return TokenPayload(
            user_id=user_id,
            email="test@example.com",
            role="STUDENT",
        )

    def revoke_refresh_token(self, token: str) -> None:
        self._revoked.add(token)

    def revoke_all_tokens_for_users(self, user_id: UUID) -> None:
        self._revoked_users.add(user_id)

    def generate_reset_token(self, user) -> str:
        return f"fake_reset_{user.id}"

    def validate_reset_token(self, token: str) -> TokenPayload:
        if token in self._revoked:
            raise InvalidTokenError()
        user_id = UUID(token.replace("fake_reset_", ""))
        return TokenPayload(
            user_id=user_id,
            email="test@example.com",
            role="STUDENT",
        )


class FakePasswordHasher(PasswordHasherPort):
    """
    Does not actually hash — just prefixes with 'hashed_'
    so tests can verify the right value was stored.
    """

    def hash(self, plain_password: str) -> str:
        return f"hashed_{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed_{plain_password}"


class FakeOtpService(OtpServicePort):
    """
    Stores OTPs in memory. Always generates '123456' for predictability.
    """

    def __init__(self):
        self._store: dict[str, str] = {}

    def generate_and_store_otp(self, email: str) -> str:
        otp = "123456"
        self._store[email] = otp
        return otp

    def verify_otp(self, email: str, otp: str) -> bool:
        stored = self._store.get(email)
        if stored and stored == otp:
            del self._store[email]
            return True
        return False


class FakeEmailService(EmailServicePort):
    """
    Records sent emails so tests can verify the right emails were sent.
    """

    def __init__(self):
        self.sent_otp_emails: list[dict] = []
        self.sent_temp_password_emails: list[dict] = []

    def send_otp_email(self, to_email: str, otp: str) -> None:
        self.sent_otp_emails.append({
            "to": to_email,
            "otp": otp,
        })

    def send_temporary_password_email(
        self,
        to_email: str,
        full_name: str,
        temporary_password: str,
    ) -> None:
        self.sent_temp_password_emails.append({
            "to": to_email,
            "full_name": full_name,
            "temp_password": temporary_password,
        })


class FakeOAuthProvider(OAuthProviderPort):
    """
    Returns a hardcoded profile for testing OAuth flows.
    """

    def __init__(self, profile: OAuthUserProfile):
        self._profile = profile

    def get_user_profile(self, authorization_code: str) -> OAuthUserProfile:
        return self._profile