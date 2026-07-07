"""
DRF serializers — validate incoming request payloads and format outgoing
response payloads for the inbound REST adapter.

Response serializer field names (userId, nested `user` in AuthResponse,
mustChangePassword/oauthProviders/updatedAt on AccountResponse, etc.) are
confirmed against the project's actual OpenAPI spec — not guessed.

Two serializers expect an assembled dict/object rather than a single
domain object directly, since their JSON shape combines data that doesn't
live on one dataclass:

  AuthResponseSerializer expects:
      {"access_token": ..., "refresh_token": ..., "token_type": ...,
       "expires_in": ..., "user": <domain User>}
      i.e. a TokenPair's fields plus the authenticated user, not just
      the TokenPair alone.

  OtpVerifiedResponseSerializer expects:
      {"reset_token": <str from generate_reset_token()>, "expires_in": 300}
      since TokenServicePort.generate_reset_token() returns a bare string,
      not an object carrying its own expiry.

Enum fields (role, status, oauthProviders) are surfaced via
SerializerMethodField rather than a plain CharField. This is deliberate:
domain enums are (str, Enum) subclasses, and prior to Python 3.11,
str(SomeStrEnum.MEMBER) returns "SomeStrEnum.MEMBER" rather than the plain
value — a well-known gotcha. Using obj.<field>.value explicitly avoids
depending on Python version behavior.
"""
from rest_framework import serializers

from domain.enums import UserRole

PASSWORD_MIN_LENGTH = 8
FULL_NAME_MIN_LENGTH = 2
FULL_NAME_MAX_LENGTH = 100
OTP_PATTERN = r"^\d{6}$"


# ---------------------------------------------------------------------
# Request serializers
# ---------------------------------------------------------------------

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    fullName = serializers.CharField(
        min_length=FULL_NAME_MIN_LENGTH, max_length=FULL_NAME_MAX_LENGTH
    )
    password = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, write_only=True)
    confirmPassword = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirmPassword"]:
            raise serializers.ValidationError(
                {"confirmPassword": "Passwords do not match."}
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    refreshToken = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refreshToken = serializers.CharField()


class OAuthCallbackSerializer(serializers.Serializer):
    """
    Validates query params on GET /auth/oauth/{provider}/callback.
    Not tied to a named request schema in the spec (OAuth callbacks pass
    code/state as query params, not a JSON body), but validating them
    here keeps that logic out of the view per the "views contain no
    business logic" rule.
    """

    code = serializers.CharField()
    state = serializers.CharField(required=False, allow_blank=True)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.RegexField(
        regex=OTP_PATTERN,
        error_messages={"invalid": "OTP must be exactly 6 digits."},
    )


class OtpVerifiedResponseSerializer(serializers.Serializer):
    """Formats the response for POST /auth/password/verify-otp."""

    resetToken = serializers.CharField(source="reset_token")
    expiresIn = serializers.IntegerField(source="expires_in")


class ResetPasswordSerializer(serializers.Serializer):
    resetToken = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, write_only=True)
    confirmPassword = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["newPassword"] != attrs["confirmPassword"]:
            raise serializers.ValidationError(
                {"confirmPassword": "Passwords do not match."}
            )
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(min_length=PASSWORD_MIN_LENGTH, write_only=True)
    confirmPassword = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["newPassword"] != attrs["confirmPassword"]:
            raise serializers.ValidationError(
                {"confirmPassword": "Passwords do not match."}
            )
        return attrs


class CreateAccountSerializer(serializers.Serializer):
    """
    Admin-only: creates an account for a Teacher or Admin. Students only
    ever arrive via self-registration (/auth/register) — STUDENT is
    deliberately excluded from the allowed choices here.
    A temporary password is generated server-side and emailed to the
    new user (see EmailServicePort.send_temporary_password_email).
    """

    email = serializers.EmailField()
    fullName = serializers.CharField(
        min_length=FULL_NAME_MIN_LENGTH, max_length=FULL_NAME_MAX_LENGTH
    )
    role = serializers.ChoiceField(
        choices=[
            (r.value, r.name) for r in UserRole if r != UserRole.STUDENT
        ]
    )


# ---------------------------------------------------------------------
# Response serializers
# ---------------------------------------------------------------------

class CurrentUserResponseSerializer(serializers.Serializer):
    """Formats a domain User for GET /auth/me. Also embedded (as `user`)
    inside AuthResponseSerializer."""

    userId = serializers.UUIDField(source="id")
    email = serializers.EmailField()
    fullName = serializers.CharField(source="full_name")
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    oauthProviders = serializers.SerializerMethodField()
    mustChangePassword = serializers.BooleanField(source="must_change_password")
    createdAt = serializers.DateTimeField(source="created_at")

    def get_role(self, obj) -> str:
        return obj.role.value

    def get_status(self, obj) -> str:
        return obj.status.value

    def get_oauthProviders(self, obj) -> list[str]:
        return [provider.value for provider in obj.oauth_providers]


class AuthResponseSerializer(serializers.Serializer):
    """
    Formats the combined token + user payload for login/register/refresh/
    OAuth responses.

    IMPORTANT: unlike a plain TokenPair, this serializer expects an
    instance (or dict) that ALSO carries the authenticated user, e.g.:

        AuthResponseSerializer({
            "access_token": pair.access_token,
            "refresh_token": pair.refresh_token,
            "token_type": pair.token_type,
            "expires_in": pair.expires_in,
            "user": user,   # the domain User dataclass
        }).data

    The calling view/use-case is responsible for assembling this combined
    structure — TokenPair alone does not include `user`.
    """

    accessToken = serializers.CharField(source="access_token")
    refreshToken = serializers.CharField(source="refresh_token")
    tokenType = serializers.CharField(source="token_type")
    expiresIn = serializers.IntegerField(source="expires_in")
    user = CurrentUserResponseSerializer()


class AccountResponseSerializer(serializers.Serializer):
    """Formats a domain User for admin account-management responses."""

    userId = serializers.UUIDField(source="id")
    email = serializers.EmailField()
    fullName = serializers.CharField(source="full_name")
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    mustChangePassword = serializers.BooleanField(source="must_change_password")
    oauthProviders = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")

    def get_role(self, obj) -> str:
        return obj.role.value

    def get_status(self, obj) -> str:
        return obj.status.value

    def get_oauthProviders(self, obj) -> list[str]:
        return [provider.value for provider in obj.oauth_providers]