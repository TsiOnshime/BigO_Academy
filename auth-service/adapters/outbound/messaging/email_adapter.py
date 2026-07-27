from django.conf import settings
from django.core.mail import send_mail

from application.ports.outbound.email_service import EmailServicePort


class DjangoEmailService(EmailServicePort):
    """send_mail-backed implementation of EmailServicePort."""

    def send_otp_email(self, to_email: str, otp: str) -> None:
        send_mail(
            subject="Your BigO Academy password reset code",
            message=f"Your reset code is: {otp}. Valid for 10 minutes.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[to_email],
            fail_silently=False,
        )

    def send_temporary_password_email(
        self, to_email: str, full_name: str, temp_pass: str
    ) -> None:
        send_mail(
            subject="Welcome to BigO Academy — Your temporary password",
            message=(
                f"Hi {full_name}, your temp password is: {temp_pass}. "
                f"Please change it on first login."
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[to_email],
            fail_silently=False,
        )