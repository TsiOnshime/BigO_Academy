"""
Google OAuth 2.0 adapter implementing OAuthProviderPort.

Requires these settings (via python-decouple, matching the project's
existing .env pattern):
    GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET
    GOOGLE_REDIRECT_URI   e.g. http://localhost:8080/api/v1/auth/oauth/google/callback
"""
from urllib.parse import urlencode

import requests
from django.conf import settings

from application.ports.outbound.oauth_provider import OAuthProviderPort, OAuthUserProfile
from domain.exceptions import InvalidTokenError

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

REQUEST_TIMEOUT_SECONDS = 10


class GoogleOAuthAdapter(OAuthProviderPort):
    def get_authorization_url(self, state: str | None = None) -> str:
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    def get_user_profile(self, authorization_code: str) -> OAuthUserProfile:
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": authorization_code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if token_response.status_code != 200:
            raise InvalidTokenError("Invalid or expired Google authorization code.")

        access_token = token_response.json().get("access_token")
        if not access_token:
            raise InvalidTokenError("Google did not return an access token.")

        profile_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if profile_response.status_code != 200:
            raise InvalidTokenError("Failed to fetch Google user profile.")

        data = profile_response.json()
        email = data.get("email")
        if not email:
            raise InvalidTokenError("Google profile did not include an email address.")

        return OAuthUserProfile(
            email=email,
            full_name=data.get("name", ""),
            provider="GOOGLE",
            provider_user_id=data.get("sub", ""),
        )