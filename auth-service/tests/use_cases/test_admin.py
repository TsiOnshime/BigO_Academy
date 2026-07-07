import pytest
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from domain.exceptions import EmailAlreadyExistsError, UserNotFoundError, InvalidTokenError
from application.use_cases.create_account import CreateAccountUseCase, CreateAccountCommand
from application.use_cases.get_account import GetAccountUseCase, GetAccountCommand
from application.use_cases.activate_account import ActivateAccountUseCase, ActivateAccountCommand
from application.use_cases.deactivate_account import DeactivateAccountUseCase, DeactivateAccountCommand
from application.use_cases.admin_reset_password import AdminResetPasswordUseCase, AdminResetPasswordCommand
from tests.fakes import (
    FakeUserRepository,
    FakeTokenService,
    FakePasswordHasher,
    FakeEmailService,
)


# ── Helpers ───────────────────────────────────────────────────────────────

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


# ── CreateAccount Tests ───────────────────────────────────────────────────

class TestCreateAccount:

    def make_use_case(self, repo=None, password_hasher=None, email_service=None):
        return CreateAccountUseCase(
            user_repository=repo or FakeUserRepository(),
            password_hasher=password_hasher or FakePasswordHasher(),
            email_service=email_service or FakeEmailService(),
        )

    def test_creates_teacher_account_successfully(self):
        """
        Admin creates a teacher account — should succeed and
        return the created user.
        """
        repo = FakeUserRepository()
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(CreateAccountCommand(
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
            role=UserRole.TEACHER,
        ))

        assert result.user.email == "meron@a2sv.org"
        assert result.user.role == UserRole.TEACHER

    def test_creates_admin_account_successfully(self):
        """Admin can also create another Admin account."""
        repo = FakeUserRepository()
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(CreateAccountCommand(
            full_name="Admin User",
            email="admin@a2sv.org",
            role=UserRole.ADMIN,
        ))

        assert result.user.role == UserRole.ADMIN

    def test_new_account_starts_inactive(self):
        """
        Admin-created accounts start as INACTIVE — they must be
        explicitly activated before the user can log in.
        """
        repo = FakeUserRepository()
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(CreateAccountCommand(
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
            role=UserRole.TEACHER,
        ))

        assert result.user.status == AccountStatus.INACTIVE

    def test_new_account_must_change_password(self):
        """
        Admin-created accounts get a temporary password —
        must_change_password must be True.
        """
        repo = FakeUserRepository()
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(CreateAccountCommand(
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
            role=UserRole.TEACHER,
        ))

        assert result.user.must_change_password is True

    def test_sends_temporary_password_email(self):
        """
        After creating the account, a temporary password email
        must be sent to the new user's address.
        """
        repo = FakeUserRepository()
        email_service = FakeEmailService()
        use_case = self.make_use_case(repo=repo, email_service=email_service)

        use_case.execute(CreateAccountCommand(
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
            role=UserRole.TEACHER,
        ))

        assert len(email_service.sent_temp_password_emails) == 1
        assert email_service.sent_temp_password_emails[0]["to"] == "meron@a2sv.org"

    def test_duplicate_email_raises_error(self):
        """
        Creating an account with an already registered email
        raises EmailAlreadyExistsError.
        """
        repo = FakeUserRepository()
        make_active_user(repo, email="meron@a2sv.org")
        use_case = self.make_use_case(repo=repo)

        with pytest.raises(EmailAlreadyExistsError):
            use_case.execute(CreateAccountCommand(
                full_name="Meron Tadesse",
                email="meron@a2sv.org",
                role=UserRole.TEACHER,
            ))

    def test_password_is_hashed(self):
        """
        The temporary password must be stored hashed, never plain text.
        """
        repo = FakeUserRepository()
        use_case = self.make_use_case(repo=repo)

        use_case.execute(CreateAccountCommand(
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
            role=UserRole.TEACHER,
        ))

        saved = repo.find_by_email("meron@a2sv.org")
        assert saved.hashed_password.startswith("hashed_")


# ── GetAccount Tests ──────────────────────────────────────────────────────

class TestGetAccount:

    def make_use_case(self, repo=None):
        return GetAccountUseCase(
            user_repository=repo or FakeUserRepository(),
        )

    def test_returns_existing_user(self):
        """Admin can fetch any user by their ID."""
        repo = FakeUserRepository()
        user = make_active_user(repo)
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(GetAccountCommand(user_id=user.id))

        assert result.id == user.id
        assert result.email == user.email

    def test_nonexistent_user_raises_error(self):
        """Fetching a user that doesn't exist raises UserNotFoundError."""
        use_case = self.make_use_case()

        with pytest.raises(UserNotFoundError):
            use_case.execute(GetAccountCommand(user_id=uuid4()))


# ── ActivateAccount Tests ─────────────────────────────────────────────────

class TestActivateAccount:

    def make_use_case(self, repo=None):
        return ActivateAccountUseCase(
            user_repository=repo or FakeUserRepository(),
        )

    def test_activates_inactive_account(self):
        """
        Activating an INACTIVE account sets its status to ACTIVE.
        """
        repo = FakeUserRepository()
        user = make_active_user(repo, status=AccountStatus.INACTIVE)
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(ActivateAccountCommand(user_id=user.id))

        assert result.status == AccountStatus.ACTIVE

    def test_activating_already_active_account_is_safe(self):
        """
        Activating an already ACTIVE account should succeed silently —
        idempotent operation, no error raised.
        """
        repo = FakeUserRepository()
        user = make_active_user(repo, status=AccountStatus.ACTIVE)
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(ActivateAccountCommand(user_id=user.id))

        assert result.status == AccountStatus.ACTIVE

    def test_nonexistent_user_raises_error(self):
        """Activating a nonexistent user raises UserNotFoundError."""
        use_case = self.make_use_case()

        with pytest.raises(UserNotFoundError):
            use_case.execute(ActivateAccountCommand(user_id=uuid4()))


# ── DeactivateAccount Tests ───────────────────────────────────────────────

class TestDeactivateAccount:

    def make_use_case(self, repo=None, token_service=None):
        return DeactivateAccountUseCase(
            user_repository=repo or FakeUserRepository(),
            token_service=token_service or FakeTokenService(),
        )

    def test_deactivates_active_account(self):
        """
        Deactivating an ACTIVE account sets its status to INACTIVE.
        """
        repo = FakeUserRepository()
        user = make_active_user(repo)
        use_case = self.make_use_case(repo=repo)

        result = use_case.execute(DeactivateAccountCommand(user_id=user.id))

        assert result.status == AccountStatus.INACTIVE

    def test_deactivation_revokes_all_tokens(self):
        """
        Deactivating an account must immediately revoke all refresh
        tokens — the user can no longer use existing sessions.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        refresh_token = token_service.generate_tokens(user).refresh_token
        use_case = self.make_use_case(repo=repo, token_service=token_service)

        use_case.execute(DeactivateAccountCommand(user_id=user.id))

        with pytest.raises(InvalidTokenError):
            token_service.validate_refresh_token(refresh_token)

    def test_nonexistent_user_raises_error(self):
        """Deactivating a nonexistent user raises UserNotFoundError."""
        use_case = self.make_use_case()

        with pytest.raises(UserNotFoundError):
            use_case.execute(DeactivateAccountCommand(user_id=uuid4()))


# ── AdminResetPassword Tests ──────────────────────────────────────────────

class TestAdminResetPassword:

    def make_use_case(
        self, repo=None, token_service=None,
        password_hasher=None, email_service=None
    ):
        return AdminResetPasswordUseCase(
            user_repository=repo or FakeUserRepository(),
            token_service=token_service or FakeTokenService(),
            password_hasher=password_hasher or FakePasswordHasher(),
            email_service=email_service or FakeEmailService(),
        )

    def test_resets_password_successfully(self):
        """
        Admin force-resetting a password should change the stored hash.
        """
        repo = FakeUserRepository()
        user = make_active_user(repo, hashed_password="hashed_OldPass!")
        use_case = self.make_use_case(repo=repo)

        use_case.execute(AdminResetPasswordCommand(user_id=user.id))

        updated = repo.find_by_email("abel@example.com")
        assert updated.hashed_password != "hashed_OldPass!"
        assert updated.hashed_password.startswith("hashed_")

    def test_sets_must_change_password_true(self):
        """
        After admin reset, must_change_password must be True —
        the user must change it on next login.
        """
        repo = FakeUserRepository()
        user = make_active_user(repo, must_change_password=False)
        use_case = self.make_use_case(repo=repo)

        use_case.execute(AdminResetPasswordCommand(user_id=user.id))

        updated = repo.find_by_email("abel@example.com")
        assert updated.must_change_password is True

    def test_sends_temporary_password_email(self):
        """
        A temporary password email must be sent to the user
        after admin resets their password.
        """
        repo = FakeUserRepository()
        email_service = FakeEmailService()
        user = make_active_user(repo)
        use_case = self.make_use_case(repo=repo, email_service=email_service)

        use_case.execute(AdminResetPasswordCommand(user_id=user.id))

        assert len(email_service.sent_temp_password_emails) == 1
        assert email_service.sent_temp_password_emails[0]["to"] == "abel@example.com"

    def test_revokes_all_tokens(self):
        """
        Admin password reset must revoke all existing refresh tokens.
        """
        repo = FakeUserRepository()
        token_service = FakeTokenService()
        user = make_active_user(repo)
        refresh_token = token_service.generate_tokens(user).refresh_token
        use_case = self.make_use_case(repo=repo, token_service=token_service)

        use_case.execute(AdminResetPasswordCommand(user_id=user.id))

        with pytest.raises(InvalidTokenError):
            token_service.validate_refresh_token(refresh_token)

    def test_nonexistent_user_raises_error(self):
        """Admin resetting a nonexistent user raises UserNotFoundError."""
        use_case = self.make_use_case()

        with pytest.raises(UserNotFoundError):
            use_case.execute(AdminResetPasswordCommand(user_id=uuid4()))