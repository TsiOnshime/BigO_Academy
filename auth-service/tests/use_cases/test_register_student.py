import pytest
from uuid import uuid4

from domain.enums import UserRole, AccountStatus
from domain.exceptions import PasswordMismatchError, EmailAlreadyExistsError
from domain.models import User
from application.use_cases.register_student import (
    RegisterStudentUseCase,
    RegisterStudentCommand,
)
from tests.fakes import FakeUserRepository, FakeTokenService, FakePasswordHasher


# ── Helpers ───────────────────────────────────────────────────────────────

def make_use_case(repo=None, token_service=None, password_hasher=None):
    """
    Factory function that builds a RegisterStudentUseCase
    with fake dependencies. Any fake not provided gets a fresh default.
    This avoids repeating the same setup in every test.
    """
    return RegisterStudentUseCase(
        user_repository=repo or FakeUserRepository(),
        token_service=token_service or FakeTokenService(),
        password_hasher=password_hasher or FakePasswordHasher(),
    )


def make_command(**overrides):
    """
    Builds a valid RegisterStudentCommand.
    Any field can be overridden per test using keyword arguments.
    Example: make_command(email="other@test.com")
    """
    defaults = {
        "full_name": "Abel Girma",
        "email": "abel@example.com",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
    }
    defaults.update(overrides)
    return RegisterStudentCommand(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────

class TestRegisterStudent:

    def test_successful_registration_returns_tokens(self):
        """
        Happy path — valid input should return access and refresh tokens.
        """
        # Arrange
        use_case = make_use_case()
        command = make_command()

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "Bearer"
        assert result.expires_in == 900

    def test_successful_registration_returns_correct_user(self):
        """
        The returned user should have the correct email, name, and role.
        """
        use_case = make_use_case()
        command = make_command()

        result = use_case.execute(command)

        assert result.user.email == "abel@example.com"
        assert result.user.full_name == "Abel Girma"
        assert result.user.role == UserRole.STUDENT

    def test_registered_user_is_active(self):
        """
        A newly registered student should always start as ACTIVE.
        """
        use_case = make_use_case()
        result = use_case.execute(make_command())

        assert result.user.status == AccountStatus.ACTIVE

    def test_registered_user_must_change_password_is_false(self):
        """
        Students choose their own password — must_change_password
        should be False, unlike admin-created accounts.
        """
        use_case = make_use_case()
        result = use_case.execute(make_command())

        assert result.user.must_change_password is False

    def test_password_is_hashed_not_stored_in_plain_text(self):
        """
        The stored password should be hashed, never plain text.
        FakePasswordHasher prefixes with 'hashed_' so we can verify.
        """
        repo = FakeUserRepository()
        use_case = make_use_case(repo=repo)
        command = make_command(password="SecurePass123!",
                            confirm_password="SecurePass123!")

        result = use_case.execute(command)

        # Fetch the saved user from the fake repo
        saved_user = repo.find_by_email("abel@example.com")
        assert saved_user.hashed_password == "hashed_SecurePass123!"
        assert saved_user.hashed_password != "SecurePass123!"

    def test_user_is_saved_to_repository(self):
        """
        After registration the user should exist in the repository.
        """
        repo = FakeUserRepository()
        use_case = make_use_case(repo=repo)

        use_case.execute(make_command())

        assert repo.email_exists("abel@example.com") is True

    def test_password_mismatch_raises_error(self):
        """
        If password and confirmPassword don't match,
        PasswordMismatchError should be raised.
        """
        use_case = make_use_case()
        command = make_command(
            password="SecurePass123!",
            confirm_password="DifferentPass456!",
        )

        with pytest.raises(PasswordMismatchError):
            use_case.execute(command)

    def test_password_mismatch_does_not_save_user(self):
        """
        If passwords don't match, no user should be created.
        """
        repo = FakeUserRepository()
        use_case = make_use_case(repo=repo)
        command = make_command(
            password="SecurePass123!",
            confirm_password="DifferentPass456!",
        )

        with pytest.raises(PasswordMismatchError):
            use_case.execute(command)

        assert repo.email_exists("abel@example.com") is False

    def test_duplicate_email_raises_error(self):
        """
        If the email is already registered,
        EmailAlreadyExistsError should be raised.
        """
        repo = FakeUserRepository()
        use_case = make_use_case(repo=repo)

        # Register once successfully
        use_case.execute(make_command())

        # Try to register again with the same email
        with pytest.raises(EmailAlreadyExistsError):
            use_case.execute(make_command())

    def test_duplicate_email_error_contains_email(self):
        """
        The error should carry the duplicate email for debugging.
        """
        repo = FakeUserRepository()
        use_case = make_use_case(repo=repo)
        use_case.execute(make_command())

        with pytest.raises(EmailAlreadyExistsError) as exc_info:
            use_case.execute(make_command())

        assert exc_info.value.email == "abel@example.com"

    def test_different_emails_can_both_register(self):
        """
        Two different emails should both register successfully.
        """
        repo = FakeUserRepository()
        use_case = make_use_case(repo=repo)

        use_case.execute(make_command(email="abel@example.com"))
        use_case.execute(make_command(email="meron@example.com"))

        assert repo.email_exists("abel@example.com") is True
        assert repo.email_exists("meron@example.com") is True

    def test_registered_user_has_no_oauth_providers(self):
        """
        A student registering with email/password should have
        no OAuth providers linked initially.
        """
        use_case = make_use_case()
        result = use_case.execute(make_command())

        assert result.user.oauth_providers == []