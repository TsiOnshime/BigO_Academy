import pytest
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from application.use_cases.forgot_password import ForgotPasswordUseCase, ForgotPasswordCommand
from tests.fakes import (
    FakeUserRepository,
    FakeOtpService,
    FakeEmailService,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def make_use_case(repo=None, otp_service=None, email_service=None):
    return ForgotPasswordUseCase(
        user_repository=repo or FakeUserRepository(),
        otp_service=otp_service or FakeOtpService(),
        email_service=email_service or FakeEmailService(),
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

class TestForgotPassword:

    def test_sends_otp_email_to_registered_user(self):
        """
        Happy path — if the email exists, an OTP email should be sent.
        """
        repo = FakeUserRepository()
        otp_service = FakeOtpService()
        email_service = FakeEmailService()
        make_active_user(repo)
        use_case = make_use_case(
            repo=repo,
            otp_service=otp_service,
            email_service=email_service,
        )

        use_case.execute(ForgotPasswordCommand(email="abel@example.com"))

        assert len(email_service.sent_otp_emails) == 1
        assert email_service.sent_otp_emails[0]["to"] == "abel@example.com"

    def test_otp_sent_in_email_matches_stored_otp(self):
        """
        The OTP in the email must match what was stored —
        otherwise the user can never verify it.
        """
        repo = FakeUserRepository()
        otp_service = FakeOtpService()
        email_service = FakeEmailService()
        make_active_user(repo)
        use_case = make_use_case(
            repo=repo,
            otp_service=otp_service,
            email_service=email_service,
        )

        use_case.execute(ForgotPasswordCommand(email="abel@example.com"))

        sent_otp = email_service.sent_otp_emails[0]["otp"]
        # FakeOtpService always generates "123456"
        assert sent_otp == "123456"

    def test_unregistered_email_sends_no_email(self):
        """
        Security: if the email is not registered, no email is sent
        and no error is raised — prevents email enumeration attacks.
        """
        email_service = FakeEmailService()
        use_case = make_use_case(email_service=email_service)

        # Should not raise — always returns silently
        use_case.execute(ForgotPasswordCommand(email="nobody@example.com"))

        assert len(email_service.sent_otp_emails) == 0

    def test_unregistered_email_does_not_raise_error(self):
        """
        The use case must never reveal whether an email is registered.
        Calling with an unknown email should complete silently.
        """
        use_case = make_use_case()

        # Must not raise any exception
        use_case.execute(ForgotPasswordCommand(email="ghost@example.com"))

    def test_otp_is_stored_for_correct_email(self):
        """
        The OTP should be stored against the correct email
        so verify_otp can find it later.
        """
        repo = FakeUserRepository()
        otp_service = FakeOtpService()
        email_service = FakeEmailService()
        make_active_user(repo)
        use_case = make_use_case(
            repo=repo,
            otp_service=otp_service,
            email_service=email_service,
        )

        use_case.execute(ForgotPasswordCommand(email="abel@example.com"))

        # The OTP should now be verifiable
        assert otp_service.verify_otp("abel@example.com", "123456") is True