"""
GET /auth/oauth/google, /auth/oauth/google/callback
GET /auth/oauth/github, /auth/oauth/github/callback

Uses the CONFIRMED OAuthLoginCommand/OAuthLoginResult (real file
shared).
"""
from urllib.parse import urlencode, quote_plus
from decouple import config
from application.use_cases.oauth_login import OAuthLoginCommand
from django.http import HttpResponseRedirect
from domain.enums import OAuthProvider
from infrastructure.config.dependencies import (
    get_github_oauth_adapter,
    get_github_oauth_login_use_case,
    get_google_oauth_adapter,
    get_google_oauth_login_use_case,
)
from rest_framework.response import Response

from ..serializers import AuthResponseSerializer, OAuthCallbackSerializer
from .base import BaseAuthView

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5174')


class GoogleOAuthInitiateView(BaseAuthView):
    def get(self, request):
        state = request.query_params.get("state")
        adapter = get_google_oauth_adapter()
        return HttpResponseRedirect(adapter.get_authorization_url(state=state))


class GoogleOAuthCallbackView(BaseAuthView):
    def get(self, request):
        serializer = OAuthCallbackSerializer(data=request.query_params)
        if not serializer.is_valid():
            return HttpResponseRedirect(f"{FRONTEND_URL}/login?error=Invalid+OAuth+callback")

        try:
            use_case = get_google_oauth_login_use_case()
            result = use_case.execute(
                OAuthLoginCommand(
                    authorization_code=serializer.validated_data["code"],
                    provider=OAuthProvider.GOOGLE,
                )
            )
            query_params = urlencode({
                "accessToken": result.access_token,
                "refreshToken": result.refresh_token,
                "role": result.user.role.value if hasattr(result.user.role, 'value') else str(result.user.role),
                "email": result.user.email,
                "fullName": result.user.full_name,
                "userId": str(result.user.id),
            })
            return HttpResponseRedirect(f"{FRONTEND_URL}/oauth/callback?{query_params}")
        except Exception as exc:
            err_msg = quote_plus(str(exc))
            return HttpResponseRedirect(f"{FRONTEND_URL}/login?error={err_msg}")


class GitHubOAuthInitiateView(BaseAuthView):
    def get(self, request):
        state = request.query_params.get("state")
        adapter = get_github_oauth_adapter()
        return HttpResponseRedirect(adapter.get_authorization_url(state=state))


class GitHubOAuthCallbackView(BaseAuthView):
    def get(self, request):
        serializer = OAuthCallbackSerializer(data=request.query_params)
        if not serializer.is_valid():
            return HttpResponseRedirect(f"{FRONTEND_URL}/login?error=Invalid+OAuth+callback")

        try:
            use_case = get_github_oauth_login_use_case()
            result = use_case.execute(
                OAuthLoginCommand(
                    authorization_code=serializer.validated_data["code"],
                    provider=OAuthProvider.GITHUB,
                )
            )
            query_params = urlencode({
                "accessToken": result.access_token,
                "refreshToken": result.refresh_token,
                "role": result.user.role.value if hasattr(result.user.role, 'value') else str(result.user.role),
                "email": result.user.email,
                "fullName": result.user.full_name,
                "userId": str(result.user.id),
            })
            return HttpResponseRedirect(f"{FRONTEND_URL}/oauth/callback?{query_params}")
        except Exception as exc:
            err_msg = quote_plus(str(exc))
            return HttpResponseRedirect(f"{FRONTEND_URL}/login?error={err_msg}")