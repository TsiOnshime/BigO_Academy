from abc import ABC, abstractmethod

class OtpServicePort(ABC):
    """
    Abstract contract for generating and verifying one-time password codes.
    Used exclusively for the password reset flow.
    Implemented by the adapter in adapters/outbound/persistence/.
    """
    
    @abstractmethod
    def generate_and_store_otp(self, email: str) -> str:
        """
        Generate a 6-digit OTP, store it against the email with a 10-minute expiry,
        and return the OTP string so it can be emailed to the user.
        Called on: POST /auth/password/forgot
        """
    @abstractmethod
    def verify_otp(self, email:str, otp: str) -> bool:
        """
        Check if the submitted OTP matches what was stored for this email,
        and that it hasn't expired yet.
        Invalidates the OTP after successful verification (single-use).
        Called on: POST /auth/password/verify-otp
        Returns True if valid, False if not.
        """
        