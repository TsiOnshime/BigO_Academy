"""
Shared plumbing for every view: domain-exception -> HTTP status mapping,
bearer-token extraction, admin-role gating. No endpoint-specific business
logic lives here.
"""
from datetime import datetime, timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from domain.enums import UserRole
from domain.exceptions import (
    AccountInactiveError,
    EmailAlreadyExistsError,
    IncorrectPasswordError,
    InvalidCredentialsError,
    InvalidOtpError,
    InvalidTokenError,
    PasswordMismatchError,
    UserNotFoundError,
)

from infrastructure.config.dependencies import get_token_service

# Exact mapping from spec.
EXCEPTION_STATUS_MAP = {
    EmailAlreadyExistsError: (status.HTTP_409_CONFLICT, "CONFLICT"),
    InvalidCredentialsError: (status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED"),
    AccountInactiveError: (status.HTTP_403_FORBIDDEN, "FORBIDDEN"),
    InvalidTokenError: (status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED"),
    InvalidOtpError: (status.HTTP_400_BAD_REQUEST, "BAD_REQUEST"),
    IncorrectPasswordError: (status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED"),
    UserNotFoundError: (status.HTTP_404_NOT_FOUND, "NOT_FOUND"),
    PasswordMismatchError: (status.HTTP_400_BAD_REQUEST, "BAD_REQUEST"),
}


def error_body(status_code: int, error_code: str, message: str) -> dict:
    return {
        "status": status_code,
        "error": error_code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class BaseAuthView(APIView):
    def handle_domain_exception(self, exc: Exception) -> Response:
        for exc_type, (status_code, error_code) in EXCEPTION_STATUS_MAP.items():
            if isinstance(exc, exc_type):
                return Response(error_body(status_code, error_code, str(exc)), status=status_code)
        # Not a recognized domain exception — re-raise so DRF's default
        # handling/logging takes over rather than us guessing a status.
        raise exc

    @staticmethod
    def _bearer_token(request) -> str | None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        return auth_header[len("Bearer "):]

    def authenticate(self, request):
        """Returns a TokenPayload, or raises InvalidTokenError."""
        token = self._bearer_token(request)
        if token is None:
            raise InvalidTokenError("Authentication token is missing or invalid.")
        return get_token_service().validate_access_token(token)

    @staticmethod
    def require_admin(payload) -> Response | None:
        """Returns a 403 Response if the caller isn't an admin, else None."""
        if payload.role != UserRole.ADMIN:
            return Response(
                error_body(
                    status.HTTP_403_FORBIDDEN,
                    "FORBIDDEN",
                    "You do not have permission to perform this action.",
                ),
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @staticmethod
    def auth_response_data(tokens, user) -> dict:
        """
        tokens can be any object with access_token/refresh_token/
        token_type/expires_in attributes — a TokenPair, a login Result,
        or an OAuthLoginResult all satisfy this.
        """
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in,
            "user": user,
        }