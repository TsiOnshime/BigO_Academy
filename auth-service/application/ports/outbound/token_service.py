from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


from domain.enums import UserRole
from domain.models import User


@dataclass
class TokenPair:
    """Holds an access token and refresh token together"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
    
@dataclass
class TokenPayload:
    """The data extracted from a validated JWT. This is what other services also read from the token"""
    
    user_id: UUID
    email: str
    role: UserRole
    
class TokenServicePort(ABC):
    """
    Abstract contract for JWT generation and validation.
    Implemented by the simplejwt adapter in adapters/outbound/security/.
    """
    
    @abstractmethod
    def generate_tokens(self, user: User) -> TokenPair:
        """
        Generate a fresh access + refresh token pair for a user.
        Called after: successful login, registration, OAuth login, token refresh.
        """
        
    @abstractmethod
    def validate_access_token(self, token: str) -> TokenPayload:
        """
        Validate an access token and return its payload.
        Raises InvalidTokenError if the token is expired or tampered with.
        Called on: every protected endpoint (GET /auth/me, POST /auth/logout, etc.)
        """
    
    @abstractmethod
    def validate_refresh_token(self, token: str) -> TokenPayload:
        """
        Validate a refresh token and return its payload.
        Raises InvalidTokenError if invalid or already revoked.
        Called on: POST /auth/refresh
        """
    
    @abstractmethod
    def revoke_refresh_token(self, token: str) -> None:
        """
        Invalidate a refresh token so it can never be used again.
        Called on: POST /auth/logout, POST /auth/password/change,
        POST /auth/password/reset, POST /auth/admin/accounts/{id}/deactivate
        """
    @abstractmethod
    def revoke_all_tokens_for_users(self, user_id: UUID) -> None:
        """
        Invalidate ALL refresh tokens belonging to a user.
        Called on: password reset, password change, account deactivation —
        any event that should force re-login on all devices.
        """