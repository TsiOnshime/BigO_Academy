import jwt
from django.conf import settings
from rest_framework.response import Response


class JWTAuthMixin:
    """
    Mixin that provides JWT validation for DRF views.
    Validates the Authorization: Bearer <token> header.
    Extracts userId, email, and role from the token payload.
    """

    def get_current_user(self, request) -> dict | None:
        """
        Validates the JWT and returns the payload.
        Returns None if token is missing or invalid.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def require_auth(self, request) -> dict | Response:
        """
        Returns the JWT payload if valid.
        Returns a 401 Response if not authenticated.
        """
        user = self.get_current_user(request)
        if user is None:
            return Response(
                {
                    "status": 401,
                    "error": "UNAUTHORIZED",
                    "message": "Authentication token is missing or invalid",
                },
                status=401,
            )
        return user

    def require_admin(self, request) -> dict | Response:
        """
        Returns the JWT payload if user is an ADMIN.
        Returns 401 if not authenticated, 403 if not admin.
        """
        user = self.require_auth(request)
        if isinstance(user, Response):
            return user
        if user.get("role") != "ADMIN":
            return Response(
                {
                    "status": 403,
                    "error": "FORBIDDEN",
                    "message": "You do not have permission to perform this action",
                },
                status=403,
            )
        return user

    def require_admin_or_self(
        self, request, target_id: str
    ) -> dict | Response:
        """
        Returns the JWT payload if user is ADMIN
        or if the user is accessing their own resource.
        Used for endpoints like GET /payments/students/{id}
        where students can only see their own data.
        """
        user = self.require_auth(request)
        if isinstance(user, Response):
            return user
        if user.get("role") == "ADMIN":
            return user
        if str(user.get("userId")) == str(target_id):
            return user
        return Response(
            {
                "status": 403,
                "error": "FORBIDDEN",
                "message": "You do not have permission to access this resource",
            },
            status=403,
        )