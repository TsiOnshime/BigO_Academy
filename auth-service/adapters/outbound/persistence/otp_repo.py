"""
Repository for one-time-passcode (OTP) storage and verification.

Backed by DjangoOTP (adapters/outbound/persistence/django_models.py), a
transient model — rows are deleted on successful verification (single-use)
or simply left to expire and be cleaned up separately.

Implements OtpServicePort (application/ports/otp_service_port.py — adjust
this import if your port file lives elsewhere).
"""
import random
from datetime import timedelta

from django.utils import timezone

from application.ports.outbound.otp_service import OtpServicePort
from core.models import DjangoOTP

OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 10


class OTPRepository(OtpServicePort):
    """Django ORM implementation of OtpServicePort."""

    def generate_and_store_otp(self, email: str) -> str:
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)

        DjangoOTP.objects.create(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
        )
        return otp_code

    def verify_otp(self, email: str, otp: str) -> bool:
        try:
            otp_record = DjangoOTP.objects.get(email=email, otp_code=otp)
        except DjangoOTP.DoesNotExist:
            return False

        if otp_record.expires_at < timezone.now():
            otp_record.delete()
            return False

        # Valid — single use, so delete immediately before returning True.
        otp_record.delete()
        return True