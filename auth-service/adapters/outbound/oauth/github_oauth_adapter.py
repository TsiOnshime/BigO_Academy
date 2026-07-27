"""
GitHub OAuth 2.0 adapter implementing OAuthProviderPort.

Requires these settings (via python-decouple, matching the project's
existing .env pattern):
    GITHUB_CLIENT_ID
    GITHUB_CLIENT_SECRET
    GITHUB_REDIRECT_URI   e.g. http://localhost:8080/api/v1/auth/oauth/github/callback

Note: GitHub's /user endpoint only returns `email` if the user has made
an email public. If it's null, we fall back to /user/emails to find
their verified primary address instead.
"""
from urllib.parse import urlencode

import requests
from django.conf import settings

from application.ports.outbound.oauth_provider import OAuthProviderPort, OAuthUserProfile
from domain.exceptions import InvalidTokenError

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

REQUEST_TIMEOUT_SECONDS = 10


class GitHubOAuthAdapter(OAuthProviderPort):
    def get_authorization_url(self, state: str | None = None) -> str:
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "read:user user:email",
        }
        if state:
            params["state"] = state
        return f"{GITHUB_AUTH_URL}?{urlencode(params)}"

    def get_user_profile(self, authorization_code: str) -> OAuthUserProfile:
        token_response = requests.post(
            GITHUB_TOKEN_URL,
            data={
                "code": authorization_code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if token_response.status_code != 200:
            raise InvalidTokenError("Invalid or expired GitHub authorization code.")

        access_token = token_response.json().get("access_token")
        if not access_token:
            raise InvalidTokenError("GitHub did not return an access token.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        user_response = requests.get(GITHUB_USER_URL, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        if user_response.status_code != 200:
            raise InvalidTokenError("Failed to fetch GitHub user profile.")
        user_data = user_response.json()

        email = user_data.get("email")
        if not email:
            emails_response = requests.get(
                GITHUB_EMAILS_URL, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
            )
            if emails_response.status_code == 200:
                for entry in emails_response.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry.get("email")
                        break

        if not email:
            raise InvalidTokenError(
                "GitHub account has no verified email address available."
            )

        return OAuthUserProfile(
            email=email,
            full_name=user_data.get("name") or user_data.get("login", ""),
            provider="GITHUB",
            provider_user_id=str(user_data.get("id", "")),
        )