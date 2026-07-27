"""
POST /auth/admin/accounts
GET  /auth/admin/accounts/{userId}
POST /auth/admin/accounts/{userId}/activate
POST /auth/admin/accounts/{userId}/deactivate
POST /auth/admin/accounts/{userId}/reset-password

CreateAccountCommand/CreateAccountResult are CONFIRMED (real file
shared). The other three (Activate/Deactivate/AdminResetPassword) are
GUESSED — see infrastructure/config/dependencies.py docstring.
"""
from application.use_cases.activate_account import ActivateAccountCommand
from application.use_cases.admin_reset_password import AdminResetPasswordCommand
from application.use_cases.create_account import CreateAccountCommand
from application.use_cases.deactivate_account import DeactivateAccountCommand
from application.use_cases.get_account import GetAccountCommand
from infrastructure.config.dependencies import (
    get_account_use_case,
    get_activate_account_use_case,
    get_admin_reset_password_use_case,
    get_create_account_use_case,
    get_deactivate_account_use_case,
)
from rest_framework import status
from rest_framework.response import Response

from ..serializers import AccountResponseSerializer, CreateAccountSerializer
from .base import BaseAuthView


class CreateAccountView(BaseAuthView):
    def post(self, request):
        serializer = CreateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            use_case = get_create_account_use_case()
            result = use_case.execute(
                CreateAccountCommand(
                    full_name=data["fullName"], email=data["email"], role=data["role"]
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            AccountResponseSerializer(result.user).data, status=status.HTTP_201_CREATED
        )


class GetAccountView(BaseAuthView):
    def get(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            use_case = get_account_use_case()
            account = use_case.execute(GetAccountCommand(user_id=user_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AccountResponseSerializer(account).data)


class ActivateAccountView(BaseAuthView):
    def post(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            use_case = get_activate_account_use_case()
            user = use_case.execute(ActivateAccountCommand(user_id=user_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AccountResponseSerializer(user).data)


class DeactivateAccountView(BaseAuthView):
    def post(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            use_case = get_deactivate_account_use_case()
            user = use_case.execute(DeactivateAccountCommand(user_id=user_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AccountResponseSerializer(user).data)


class AdminResetPasswordView(BaseAuthView):
    def post(self, request, user_id):
        try:
            payload = self.authenticate(request)
        except Exception as exc:
            return self.handle_domain_exception(exc)

        forbidden = self.require_admin(payload)
        if forbidden is not None:
            return forbidden

        try:
            use_case = get_admin_reset_password_use_case()
            use_case.execute(AdminResetPasswordCommand(user_id=user_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response({"message": "A temporary password has been sent to the user's email."})