import pytest
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from domain.exceptions import InvalidTokenError
from application.use_cases.logout import LogoutUseCase, LogoutCommand
from tests.fakes import FakeUserRepository, FakeTokenService


def make_use_case(token_service=None):
    return LogoutUseCase(
        token_service=token_service or FakeTokenService(),
    )



def make_user() -> User:
    return User(
        id=uuid4(),
        email="abel@example.com",
        full_name="Abel Girma",
        role=UserRole.STUDENT,
        status=AccountStatus.ACTIVE,
        hashed_password="hashed_SecurePass123!",
        oauth_providers=[],
    )

class TestLogout:

    def test_logout_with_valid_token_succeeds(self):
        """
        Happy path — logging out with a valid refresh token
        should complete without raising any error.
        """
        token_service = FakeTokenService()
        user = make_user()
        use_case = make_use_case(token_service=token_service)

        token_pair = token_service.generate_tokens(user)

        # Should not raise
        use_case.execute(LogoutCommand(refresh_token=token_pair.refresh_token))

    def test_logout_revokes_the_refresh_token(self):
        """
        After logout the refresh token must be blacklisted —
        using it again should raise InvalidTokenError.
        """
        token_service = FakeTokenService()
        user = make_user()
        use_case = make_use_case(token_service=token_service)

        token_pair = token_service.generate_tokens(user)
        use_case.execute(LogoutCommand(refresh_token=token_pair.refresh_token))

        # Token is now revoked — validating it should fail
        with pytest.raises(InvalidTokenError):
            token_service.validate_refresh_token(token_pair.refresh_token)

    def test_logout_with_invalid_token_raises_error(self):
        """
        Logging out with a garbage token should raise InvalidTokenError.
        We don't silently accept invalid tokens.
        """
        use_case = make_use_case()

        with pytest.raises(InvalidTokenError):
            use_case.execute(LogoutCommand(refresh_token="garbage_token"))

    def test_logout_with_already_revoked_token_raises_error(self):
        """
        Using an already-revoked token to logout again should fail.
        Prevents replay attacks on the logout endpoint.
        """
        token_service = FakeTokenService()
        user = make_user()
        use_case = make_use_case(token_service=token_service)

        token_pair = token_service.generate_tokens(user)

        # Logout once
        use_case.execute(LogoutCommand(refresh_token=token_pair.refresh_token))

        # Try to logout again with the same token
        with pytest.raises(InvalidTokenError):
            use_case.execute(
                LogoutCommand(refresh_token=token_pair.refresh_token)
            )