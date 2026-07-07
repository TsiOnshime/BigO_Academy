import pytest
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from domain.exceptions import InvalidCredentialsError, AccountInactiveError
from application.use_cases.login import LoginUseCase, LoginCommand
from tests.fakes import FakeUserRepository, FakeTokenService, FakePasswordHasher


# ── Helpers ───────────────────────────────────────────────────────────────

def make_use_case(repo=None, token_service=None, password_hasher=None):
    return LoginUseCase(
        user_repository=repo or FakeUserRepository(),
        token_service=token_service or FakeTokenService(),
        password_hasher=password_hasher or FakePasswordHasher(),
    )


def make_command(**overrides):
    defaults = {
        "email": "abel@example.com",
        "password": "SecurePass123!",
    }
    defaults.update(overrides)
    return LoginCommand(**defaults)


def make_active_user(repo: FakeUserRepository, **overrides) -> User:
    """
    Creates and saves an ACTIVE user in the fake repository.
    FakePasswordHasher stores passwords as 'hashed_<plain>',
    so we store 'hashed_SecurePass123!' to match the default command password.
    """
    defaults = {
        "id": uuid4(),
        "email": "abel@example.com",
        "full_name": "Abel Girma",
        "role": UserRole.STUDENT,
        "status": AccountStatus.ACTIVE,
        "hashed_password": "hashed_SecurePass123!",
    }
    defaults.update(overrides)
    user = User(**defaults)
    repo.save(user)
    return user


def make_inactive_user(repo: FakeUserRepository) -> User:
    """Creates and saves an INACTIVE user."""
    return make_active_user(repo, status=AccountStatus.INACTIVE)


# ── Tests ─────────────────────────────────────────────────────────────────

class TestLogin:

    def test_successful_login_returns_tokens(self):
        """
        Happy path — correct credentials return access and refresh tokens.
        """
        repo = FakeUserRepository()
        make_active_user(repo)
        use_case = make_use_case(repo=repo)

        result = use_case.execute(make_command())

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "Bearer"
        assert result.expires_in == 900

    def test_successful_login_returns_correct_user(self):
        """
        The returned user should match the one that logged in.
        """
        repo = FakeUserRepository()
        user = make_active_user(repo)
        use_case = make_use_case(repo=repo)

        result = use_case.execute(make_command())

        assert result.user.email == user.email
        assert result.user.full_name == user.full_name
        assert result.user.role == UserRole.STUDENT

    def test_email_not_found_raises_invalid_credentials(self):
        """
        If the email doesn't exist, InvalidCredentialsError is raised.
        We never reveal whether the email is registered or not.
        """
        repo = FakeUserRepository()
        use_case = make_use_case(repo=repo)
        # No user saved — repo is empty

        with pytest.raises(InvalidCredentialsError):
            use_case.execute(make_command(email="nobody@example.com"))

    def test_wrong_password_raises_invalid_credentials(self):
        """
        If the password is wrong, InvalidCredentialsError is raised.
        Same error as email not found — no information leakage.
        """
        repo = FakeUserRepository()
        make_active_user(repo)
        use_case = make_use_case(repo=repo)

        with pytest.raises(InvalidCredentialsError):
            use_case.execute(make_command(password="WrongPassword!"))

    def test_inactive_account_raises_account_inactive_error(self):
        """
        A deactivated account should raise AccountInactiveError,
        not InvalidCredentialsError — even with correct credentials.
        """
        repo = FakeUserRepository()
        make_inactive_user(repo)
        use_case = make_use_case(repo=repo)

        with pytest.raises(AccountInactiveError):
            use_case.execute(make_command())

    def test_inactive_account_with_wrong_password_raises_account_inactive(self):
        """
        Critical ordering test: status check happens BEFORE password check.
        An inactive account with wrong password should raise AccountInactiveError,
        not InvalidCredentialsError. This proves the ordering is correct.
        """
        repo = FakeUserRepository()
        make_inactive_user(repo)
        use_case = make_use_case(repo=repo)

        with pytest.raises(AccountInactiveError):
            use_case.execute(make_command(password="WrongPassword!"))

    def test_email_not_found_does_not_reveal_existence(self):
        """
        The error raised for missing email must be the same type
        as the error raised for wrong password — no information leakage.
        """
        repo = FakeUserRepository()
        make_active_user(repo)
        use_case = make_use_case(repo=repo)

        with pytest.raises(InvalidCredentialsError):
            use_case.execute(make_command(email="different@example.com"))

    def test_correct_password_is_verified_against_hash(self):
        """
        Login should work when password matches the stored hash.
        Verifies the password hasher is actually being used.
        """
        repo = FakeUserRepository()
        hasher = FakePasswordHasher()
        make_active_user(
            repo,
            hashed_password=hasher.hash("MyPassword99!")
        )
        use_case = make_use_case(repo=repo, password_hasher=hasher)

        result = use_case.execute(make_command(password="MyPassword99!"))

        assert result.access_token is not None

    def test_teacher_can_login(self):
        """
        Login works for all roles, not just students.
        """
        repo = FakeUserRepository()
        make_active_user(repo, role=UserRole.TEACHER)
        use_case = make_use_case(repo=repo)

        result = use_case.execute(make_command())

        assert result.user.role == UserRole.TEACHER

    def test_admin_can_login(self):
        """
        Admin accounts can also login through the same endpoint.
        """
        repo = FakeUserRepository()
        make_active_user(repo, role=UserRole.ADMIN)
        use_case = make_use_case(repo=repo)

        result = use_case.execute(make_command())

        assert result.user.role == UserRole.ADMIN