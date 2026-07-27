"""
POST /auth/password/forgot, /verify-otp, /reset, /change

NOTE: Command/Result class names below are GUESSED — see
infrastructure/config/dependencies.py docstring for what's confirmed
vs. extrapolated.
"""
from application.use_cases.change_password import ChangePasswordCommand
from application.use_cases.forgot_password import ForgotPasswordCommand
from application.use_cases.reset_password import ResetPasswordCommand
from application.use_cases.verify_otp import VerifyOtpCommand
from domain.exceptions import UserNotFoundError
from infrastructure.config.dependencies import (
    get_change_password_use_case,
    get_forgot_password_use_case,
    get_reset_password_use_case,
    get_verify_otp_use_case,
)
from rest_framework.response import Response

from ..serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    OtpVerifiedResponseSerializer,
    ResetPasswordSerializer,
    VerifyOtpSerializer,
)
from .base import BaseAuthView


class ForgotPasswordView(BaseAuthView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            use_case = get_forgot_password_use_case()
            use_case.execute(
                ForgotPasswordCommand(email=serializer.validated_data["email"])
            )
        except UserNotFoundError:
            # Deliberately swallowed: always return 200 regardless of
            # whether the email is registered (prevents user enumeration).
            pass
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            {"message": "If an account with that email exists, a reset code has been sent."}
        )


class VerifyOtpView(BaseAuthView):
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_verify_otp_use_case()
            result = use_case.execute(
                VerifyOtpCommand(email=data["email"], otp=data["otp"])
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            OtpVerifiedResponseSerializer(
                {"reset_token": result.reset_token, "expires_in": result.expires_in}
            ).data
        )


class ResetPasswordView(BaseAuthView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_reset_password_use_case()
            use_case.execute(
                ResetPasswordCommand(
                    reset_token=data["resetToken"],
                    new_password=data["newPassword"],
                    confirm_password=data["confirmPassword"],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response({"message": "Password has been reset successfully. Please log in again."})


class ChangePasswordView(BaseAuthView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payload = self.authenticate(request)
            use_case = get_change_password_use_case()
            use_case.execute(
                ChangePasswordCommand(
                    user_id=payload.user_id,
                    current_password=data["currentPassword"],
                    new_password=data["newPassword"],
                    confirm_password=data["confirmPassword"],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response({"message": "Password changed successfully. Please log in again."})