"""
POST /auth/register, /auth/login, /auth/refresh, /auth/logout
GET  /auth/me

RegisterStudentUseCase is CONFIRMED (real file shared). Login/Refresh/
Logout/GetCurrentUser Command/Result class names are GUESSED — see
infrastructure/config/dependencies.py docstring for what's confirmed
vs. extrapolated.
"""
from application.use_cases.login import LoginCommand
from application.use_cases.logout import LogoutCommand
from application.use_cases.get_current_user import GetCurrentUserCommand
from application.use_cases.refresh_token import RefreshTokenCommand
from application.use_cases.register_student import RegisterStudentCommand
from infrastructure.config.dependencies import (
    get_current_user_use_case,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_token_use_case,
    get_register_use_case,
)
from rest_framework import status
from rest_framework.response import Response

from ..serializers import (
    AuthResponseSerializer,
    CurrentUserResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
)
from .base import BaseAuthView


class RegisterView(BaseAuthView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_register_use_case()
            result = use_case.execute(
                RegisterStudentCommand(
                    full_name=data["fullName"],
                    email=data["email"],
                    password=data["password"],
                    confirm_password=data["confirmPassword"],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            AuthResponseSerializer(self.auth_response_data(result, result.user)).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(BaseAuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_login_use_case()
            result = use_case.execute(
                LoginCommand(email=data["email"], password=data["password"])
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AuthResponseSerializer(self.auth_response_data(result, result.user)).data)


class RefreshTokenView(BaseAuthView):
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            use_case = get_refresh_token_use_case()
            result = use_case.execute(
                RefreshTokenCommand(refresh_token=serializer.validated_data["refreshToken"])
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AuthResponseSerializer(self.auth_response_data(result, result.user)).data)


class LogoutView(BaseAuthView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.authenticate(request)
            use_case = get_logout_use_case()
            use_case.execute(
                LogoutCommand(refresh_token=serializer.validated_data["refreshToken"])
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(BaseAuthView):
    def get(self, request):
        try:
            payload = self.authenticate(request)
            use_case = get_current_user_use_case()
            user = use_case.execute(GetCurrentUserCommand(user_id=payload.user_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(CurrentUserResponseSerializer(user).data)