"""
GET /auth/oauth/google, /auth/oauth/google/callback
GET /auth/oauth/github, /auth/oauth/github/callback

Uses the CONFIRMED OAuthLoginCommand/OAuthLoginResult (real file
shared).
"""
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


class GoogleOAuthInitiateView(BaseAuthView):
    def get(self, request):
        state = request.query_params.get("state")
        adapter = get_google_oauth_adapter()
        return HttpResponseRedirect(adapter.get_authorization_url(state=state))


class GoogleOAuthCallbackView(BaseAuthView):
    def get(self, request):
        serializer = OAuthCallbackSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            use_case = get_google_oauth_login_use_case()
            result = use_case.execute(
                OAuthLoginCommand(
                    authorization_code=serializer.validated_data["code"],
                    provider=OAuthProvider.GOOGLE,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AuthResponseSerializer(self.auth_response_data(result, result.user)).data)


class GitHubOAuthInitiateView(BaseAuthView):
    def get(self, request):
        state = request.query_params.get("state")
        adapter = get_github_oauth_adapter()
        return HttpResponseRedirect(adapter.get_authorization_url(state=state))


class GitHubOAuthCallbackView(BaseAuthView):
    def get(self, request):
        serializer = OAuthCallbackSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            use_case = get_github_oauth_login_use_case()
            result = use_case.execute(
                OAuthLoginCommand(
                    authorization_code=serializer.validated_data["code"],
                    provider=OAuthProvider.GITHUB,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AuthResponseSerializer(self.auth_response_data(result, result.user)).data)