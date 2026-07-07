import pytest
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from domain.exceptions import InvalidOtpError
from application.use_cases.verify_otp import VerifyOtpUseCase, VerifyOtpCommand
from tests.fakes import (
    FakeUserRepository,
    FakeOtpService,
    FakeTokenService,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def make_use_case(repo=None, otp_service=None, token_service=None):
    return VerifyOtpUseCase(
        user_repository=repo or FakeUserRepository(),
        otp_service=otp_service or FakeOtpService(),
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


def setup_otp(otp_service: FakeOtpService, email: str) -> str:
    """Store an OTP for the given email and return it."""
    return otp_service.generate_and_store_otp(email)


# ── Tests ─────────────────────────────────────────────────────────────────

class TestVerifyOtp:

    def test_valid_otp_returns_reset_token(self):
        """
        Happy path — correct OTP returns a reset token.
        """
        repo = FakeUserRepository()
        otp_service = FakeOtpService()
        token_service = FakeTokenService()
        make_active_user(repo)
        setup_otp(otp_service, "abel@example.com")
        use_case = make_use_case(
            repo=repo,
            otp_service=otp_service,
            token_service=token_service,
        )

        result = use_case.execute(VerifyOtpCommand(
            email="abel@example.com",
            otp="123456",
        ))

        assert result.reset_token is not None
        assert result.expires_in == 300

    def test_wrong_otp_raises_error(self):
        """
        An incorrect OTP code should raise InvalidOtpError.
        """
        repo = FakeUserRepository()
        otp_service = FakeOtpService()
        make_active_user(repo)
        setup_otp(otp_service, "abel@example.com")
        use_case = make_use_case(repo=repo, otp_service=otp_service)

        with pytest.raises(InvalidOtpError):
            use_case.execute(VerifyOtpCommand(
                email="abel@example.com",
                otp="000000",   # wrong code
            ))

    def test_otp_for_unregistered_email_raises_error(self):
        """
        If no user exists for this email, InvalidOtpError is raised.
        We never reveal whether the email is registered.
        """
        use_case = make_use_case()

        with pytest.raises(InvalidOtpError):
            use_case.execute(VerifyOtpCommand(
                email="nobody@example.com",
                otp="123456",
            ))

    def test_otp_is_single_use(self):
        """
        After a successful OTP verification, the OTP is invalidated.
        Using it a second time should raise InvalidOtpError.
        """
        repo = FakeUserRepository()
        otp_service = FakeOtpService()
        token_service = FakeTokenService()
        make_active_user(repo)
        setup_otp(otp_service, "abel@example.com")
        use_case = make_use_case(
            repo=repo,
            otp_service=otp_service,
            token_service=token_service,
        )

        # First use — should succeed
        use_case.execute(VerifyOtpCommand(
            email="abel@example.com",
            otp="123456",
        ))

        # Second use — OTP was deleted, should fail
        with pytest.raises(InvalidOtpError):
            use_case.execute(VerifyOtpCommand(
                email="abel@example.com",
                otp="123456",
            ))

    def test_reset_token_expires_in_300_seconds(self):
        """
        The spec says reset tokens expire in 5 minutes (300 seconds).
        """
        repo = FakeUserRepository()
        otp_service = FakeOtpService()
        token_service = FakeTokenService()
        make_active_user(repo)
        setup_otp(otp_service, "abel@example.com")
        use_case = make_use_case(
            repo=repo,
            otp_service=otp_service,
            token_service=token_service,
        )

        result = use_case.execute(VerifyOtpCommand(
            email="abel@example.com",
            otp="123456",
        ))

        assert result.expires_in == 300