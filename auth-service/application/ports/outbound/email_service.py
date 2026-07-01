from abc import ABC, abstractmethod


class EmailServicePort(ABC):
    """
    Abstract contract for sending emails.
    Implemented by the Django email backend adapter
    in adapters/outbound/messaging/email_adapter.py
    """

    @abstractmethod
    def send_otp_email(self, to_email: str, otp: str) -> None:
        """
        Send a password reset OTP to the user's email address.
        Called on: POST /auth/password/forgot
        """
        

    @abstractmethod
    def send_temporary_password_email(
        self,
        to_email: str,
        full_name: str,
        temporary_password: str
    ) -> None:
        """
        Send a temporary password to a newly created Teacher or Admin account.
        Called on: POST /auth/admin/accounts
        """
        