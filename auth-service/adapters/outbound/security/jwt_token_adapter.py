"""
Implements TokenServicePort using djangorestframework-simplejwt.

IMPORTANT DESIGN NOTE — read before modifying:
simplejwt's blacklist tracking (OutstandingToken.user) is a ForeignKey to
settings.AUTH_USER_MODEL, and is normally populated by RefreshToken.for_user().
Since we deliberately do NOT use for_user() (we have a custom User dataclass,
not a Django auth user), every OutstandingToken row we create will have
user=None. That FK is therefore useless to us for lookups.

To make revoke_all_tokens_for_users() work anyway, we embed "user_id" as a
custom claim inside every refresh token's payload, and when revoking "all
tokens for a user" we scan non-blacklisted OutstandingToken rows, decode
each stored token's payload (without verifying signature/expiry — we only
need the claim, and we trust rows we ourselves wrote), and blacklist the
ones whose "user_id" claim matches. This is O(n) over outstanding tokens,
which is fine at the scale this service is expected to run at.
"""
from datetime import timedelta
from uuid import UUID

from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, Token, TokenError

from application.ports.outbound.token_service import TokenPair, TokenPayload, TokenServicePort
from domain.enums import UserRole
from domain.exceptions import InvalidTokenError
from domain.models import User

USER_ID_CLAIM = "user_id"
EMAIL_CLAIM = "email"
ROLE_CLAIM = "role"


class ResetToken(Token):
    """
    A distinct, short-lived token type used only for the password-reset
    flow. Kept separate from AccessToken/RefreshToken (different
    token_type claim) so a reset token can never be replayed as a normal
    access or refresh token, even if intercepted.
    """

    token_type = "reset"
    lifetime = timedelta(minutes=5)


class JWTTokenAdapter(TokenServicePort):
    """simplejwt-backed implementation of TokenServicePort."""

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate_tokens(self, user: User) -> TokenPair:
        # Built manually (not RefreshToken.for_user()) since `user` is our
        # domain dataclass, not a Django model instance.
        refresh = RefreshToken()
        refresh[USER_ID_CLAIM] = str(user.id)
        refresh[EMAIL_CLAIM] = user.email
        refresh[ROLE_CLAIM] = user.role.value

        # .access_token copies all claims from the refresh token onto a
        # fresh AccessToken automatically (except reserved claims like
        # exp/iat/jti), so userId/email/role land on both tokens for free.
        access = refresh.access_token

        return TokenPair(
            access_token=str(access),
            refresh_token=str(refresh),
            expires_in=int(access.lifetime.total_seconds()),
        )

    def generate_reset_token(self, user: User) -> str:
        reset_token = ResetToken()
        reset_token[USER_ID_CLAIM] = str(user.id)
        reset_token[EMAIL_CLAIM] = user.email
        reset_token[ROLE_CLAIM] = user.role.value
        return str(reset_token)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_access_token(self, token: str) -> TokenPayload:
        try:
            access = AccessToken(token)
        except TokenError as e:
            raise InvalidTokenError(str(e)) from e
        return self._to_payload(access)

    def validate_refresh_token(self, token: str) -> TokenPayload:
        try:
            # RefreshToken(...) verifies signature + expiry, and (because
            # the blacklist app is installed) also calls check_blacklist()
            # automatically — so an already-revoked token raises here too.
            refresh = RefreshToken(token)
        except TokenError as e:
            raise InvalidTokenError(str(e)) from e
        return self._to_payload(refresh)

    def validate_reset_token(self, token: str) -> TokenPayload:
        try:
            reset_token = ResetToken(token)
        except TokenError as e:
            raise InvalidTokenError(str(e)) from e
        return self._to_payload(reset_token)

    # ------------------------------------------------------------------
    # Revocation
    # ------------------------------------------------------------------

    def revoke_refresh_token(self, token: str) -> None:
        try:
            refresh = RefreshToken(token)
        except TokenError:
            # Already invalid/expired — nothing meaningful to revoke.
            return
        refresh.blacklist()

    def revoke_all_tokens_for_users(self, user_id: UUID) -> None:
        already_blacklisted_ids = BlacklistedToken.objects.values_list(
            "token_id", flat=True
        )
        candidates = OutstandingToken.objects.exclude(id__in=already_blacklisted_ids)

        for record in candidates:
            try:
                # verify=False: we only need to read the payload's claims,
                # not re-validate signature/expiry of a token we ourselves
                # issued and stored.
                decoded = RefreshToken(record.token, verify=False)
            except TokenError:
                continue

            if decoded.get(USER_ID_CLAIM) == str(user_id):
                try:
                    decoded.blacklist()
                except TokenError:
                    continue

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_payload(token) -> TokenPayload:
        return TokenPayload(
            user_id=UUID(token[USER_ID_CLAIM]),
            email=token[EMAIL_CLAIM],
            role=UserRole(token[ROLE_CLAIM]),
        )