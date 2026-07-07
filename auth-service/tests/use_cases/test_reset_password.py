import pytest
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from domain.exceptions import PasswordMismatchError, InvalidTokenError
from application.use_cases.reset_password import ResetPasswordUseCase, ResetPasswordCommand
from tests.fakes import (
    FakeUserRepository,
    FakeTokenService,
    FakePasswordHasher,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def make_use_case(repo=None, token_service=None, password_hasher=None):
    return ResetPasswordUseCase(
        user_repository=repo or FakeUserRepository(),
        token_service=token_service or FakeTokenService(),
        password_hasher=password_hasher or FakePasswordHasher(),
    )


def make_active_user(repo: FakeUserRepository, **overrides) -> User:
    defaults = {
        "id": uuid4(),
        "email": "abel@example.com",
        "full_name": "Abel Girma",
        "role": UserRole.STUDENT,
        "status": AccountStatus.ACTIVE,
        "hashed_password": "hashed_OldPass123!",
        "oauth_providers": [],
    }
    defaults.update(overrides)
    user = User(**defaults)
    repo.save(user)
    return user


# ── Tests ─────────────────────────────────────────────────────────────────

class TestResetPassword:

    def test_successful_reset_updates_password(self):
        """
        Happy path — valid reset token and matching passwords
        should update the stored hash.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        hasher = FakePasswordHasher()
        user = make_active_user(repo)
        reset_token = token_service.generate_reset_token(user)
        use_case = make_use_case(
            repo=repo,
            token_service=token_service,
            password_hasher=hasher,
        )

        use_case.execute(ResetPasswordCommand(
            reset_token=reset_token,
            new_password="NewPass456!",
            confirm_password="NewPass456!",
        ))

        updated = repo.find_by_email("abel@example.com")
        assert updated.hashed_password == "hashed_NewPass456!"

    def test_successful_reset_revokes_all_tokens(self):
        """
        After password reset, all refresh tokens must be revoked
        to force re-login on all devices.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        reset_token = token_service.generate_reset_token(user)
        refresh_token = token_service.generate_tokens(user).refresh_token
        use_case = make_use_case(repo=repo, token_service=token_service)

        use_case.execute(ResetPasswordCommand(
            reset_token=reset_token,
            new_password="NewPass456!",
            confirm_password="NewPass456!",
        ))

        # All tokens for this user should now be revoked
        with pytest.raises(InvalidTokenError):
            token_service.validate_refresh_token(refresh_token)

    def test_password_mismatch_raises_error(self):
        """
        If new_password and confirm_password don't match,
        PasswordMismatchError is raised before anything is changed.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        reset_token = token_service.generate_reset_token(user)
        use_case = make_use_case(repo=repo, token_service=token_service)

        with pytest.raises(PasswordMismatchError):
            use_case.execute(ResetPasswordCommand(
                reset_token=reset_token,
                new_password="NewPass456!",
                confirm_password="DifferentPass789!",
            ))

    def test_password_mismatch_does_not_change_password(self):
        """
        If passwords don't match, the stored password must not change.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        reset_token = token_service.generate_reset_token(user)
        use_case = make_use_case(repo=repo, token_service=token_service)

        with pytest.raises(PasswordMismatchError):
            use_case.execute(ResetPasswordCommand(
                reset_token=reset_token,
                new_password="NewPass456!",
                confirm_password="DifferentPass789!",
            ))

        unchanged = repo.find_by_email("abel@example.com")
        assert unchanged.hashed_password == "hashed_OldPass123!"

    def test_invalid_reset_token_raises_error(self):
        """
        A garbage reset token should raise InvalidTokenError.
        """
        use_case = make_use_case()

        with pytest.raises(InvalidTokenError):
            use_case.execute(ResetPasswordCommand(
                reset_token="not_a_real_token",
                new_password="NewPass456!",
                confirm_password="NewPass456!",
            ))

    def test_successful_reset_clears_must_change_password(self):
        """
        After a successful reset, must_change_password should be False —
        the user has now set their own password.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo, must_change_password=True)
        reset_token = token_service.generate_reset_token(user)
        use_case = make_use_case(repo=repo, token_service=token_service)

        use_case.execute(ResetPasswordCommand(
            reset_token=reset_token,
            new_password="NewPass456!",
            confirm_password="NewPass456!",
        ))

        updated = repo.find_by_email("abel@example.com")
        assert updated.must_change_password is False