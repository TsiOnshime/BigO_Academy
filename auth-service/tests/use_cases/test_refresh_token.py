import pytest
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from domain.exceptions import InvalidTokenError, AccountInactiveError
from application.use_cases.refresh_token import RefreshTokenUseCase, RefreshTokenCommand
from tests.fakes import FakeUserRepository, FakeTokenService


# ── Helpers ───────────────────────────────────────────────────────────────

def make_use_case(repo=None, token_service=None):
    return RefreshTokenUseCase(
        user_repository=repo or FakeUserRepository(),
        token_service=token_service or FakeTokenService(),
    )



def make_active_user(repo: FakeUserRepository, **overrides) -> User:
    defaults = {
        "id": uuid4(),
        "email": "abel@example.com",
        "full_name": "Abel Girma",
        "role": UserRole.STUDENT,
        "status": AccountStatus.ACTIVE,
        "hashed_password": "hashed_SecurePass123!",
        "oauth_providers": [],
    }
    defaults.update(overrides)
    user = User(**defaults)
    repo.save(user)
    return user

# ── Tests ─────────────────────────────────────────────────────────────────

class TestRefreshToken:

    def test_valid_refresh_token_returns_new_token_pair(self):
        """
        Happy path — a valid refresh token returns a new access
        and refresh token pair.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        use_case = make_use_case(repo=repo, token_service=token_service)

        # Generate a real fake token pair first
        token_pair = token_service.generate_tokens(user)

        result = use_case.execute(
            RefreshTokenCommand(refresh_token=token_pair.refresh_token)
        )

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "Bearer"

    def test_old_refresh_token_is_revoked_after_refresh(self):
        """
        Token rotation — the old refresh token must be invalidated
        after being used. Using it again should raise InvalidTokenError.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        use_case = make_use_case(repo=repo, token_service=token_service)

        token_pair = token_service.generate_tokens(user)
        old_refresh_token = token_pair.refresh_token

        # Use it once — this should succeed
        use_case.execute(RefreshTokenCommand(refresh_token=old_refresh_token))

        # Try to use the old token again — should fail
        with pytest.raises(InvalidTokenError):
            use_case.execute(
                RefreshTokenCommand(refresh_token=old_refresh_token)
            )

    def test_invalid_refresh_token_raises_error(self):
        """
        A garbage token string should raise InvalidTokenError.
        """
        use_case = make_use_case()

        with pytest.raises(InvalidTokenError):
            use_case.execute(
                RefreshTokenCommand(refresh_token="not_a_real_token")
            )

    def test_revoked_refresh_token_raises_error(self):
        """
        A token that has already been revoked cannot be refreshed.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        use_case = make_use_case(repo=repo, token_service=token_service)

        token_pair = token_service.generate_tokens(user)

        # Manually revoke it
        token_service.revoke_refresh_token(token_pair.refresh_token)

        with pytest.raises(InvalidTokenError):
            use_case.execute(
                RefreshTokenCommand(refresh_token=token_pair.refresh_token)
            )

    def test_inactive_user_cannot_refresh(self):
        """
        If the account was deactivated after the token was issued,
        refresh should be blocked with AccountInactiveError.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo, status=AccountStatus.INACTIVE)
        use_case = make_use_case(repo=repo, token_service=token_service)

        token_pair = token_service.generate_tokens(user)

        with pytest.raises(AccountInactiveError):
            use_case.execute(
                RefreshTokenCommand(refresh_token=token_pair.refresh_token)
            )

    def test_refresh_returns_correct_user(self):
        """
        The result should contain the correct user who owns the token.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo, email="meron@example.com")
        use_case = make_use_case(repo=repo, token_service=token_service)

        token_pair = token_service.generate_tokens(user)
        result = use_case.execute(
            RefreshTokenCommand(refresh_token=token_pair.refresh_token)
        )

        assert result.user.email == "meron@example.com"
