"""
adapters/inbound/rest/middleware.py — Academic Service

Manual JWT validation using PyJWT — these tokens are issued by Auth
Service, not by this service, so we can't use simplejwt's built-in
token-owning machinery here. JWT_SECRET_KEY must be identical to Auth
Service's .env or every validation below will fail with InvalidTokenError.
"""
import jwt
from django.conf import settings

from domain.exceptions import UnauthorizedAccessError


def validate_token(authorization_header: str) -> dict:
    """
    Extract and validate the JWT from an Authorization header.

    Returns the token payload, e.g. {"user_id": ..., "email": ..., "role": ...}
    (auth-service's JWTTokenAdapter sets USER_ID_CLAIM = "user_id", not
    "userId" — confirmed against adapters/outbound/security/
    jwt_token_adapter.py).
    Raises UnauthorizedAccessError if the header is missing/malformed, the
    token is expired, or the token is otherwise invalid.
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise UnauthorizedAccessError("Missing or invalid Authorization header")

    token = authorization_header.split(" ", 1)[1].strip()
    if not token:
        raise UnauthorizedAccessError("Missing or invalid Authorization header")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedAccessError("Token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedAccessError("Invalid token")

    return payload


def require_role(payload: dict, *allowed_roles: str) -> None:
    """
    Convenience helper for views: raise UnauthorizedAccessError unless
    payload['role'] is one of allowed_roles.

    Usage in a view:
        payload = validate_token(request.META.get('HTTP_AUTHORIZATION', ''))
        require_role(payload, 'ADMIN')
    """
    role = payload.get("role")
    if role not in allowed_roles:
        raise UnauthorizedAccessError(
            f"Role '{role}' is not permitted to perform this action"
        )