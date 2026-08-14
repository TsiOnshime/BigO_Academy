"""
adapters/inbound/rest/views/base.py — Academic Service

Shared plumbing for every view: domain-exception -> HTTP status mapping,
bearer-token extraction/validation (delegated to
adapters.inbound.rest.middleware, which already implements JWT decoding
against Auth Service's shared secret), and role gating. No
endpoint-specific business logic lives here — mirrors the pattern used
in auth-service/adapters/inbound/rest/views/base.py.
"""
from datetime import datetime, timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from domain.exceptions import (
    CohortArchivedError,
    CohortNotFoundError,
    ContestNotFinishedError,
    ContestNotFoundError,
    ContestResultsAlreadySubmittedError,
    InvalidStudentStatusTransitionError,
    MentorshipNotFoundError,
    MentorshipSessionNotFoundError,
    ProblemNotFoundError,
    SessionNotFoundError,
    StudentAlreadyExistsError,
    StudentAlreadyInCohortError,
    StudentNotEligibleForGraduationError,
    StudentNotEligibleForPromotionError,
    StudentNotFoundError,
    TeacherAlreadyExistsError,
    TeacherAlreadyInCohortError,
    TeacherNotFoundError,
    TopicNotFoundError,
    UnauthorizedAccessError,
    WarningAlreadyDismissedError,
    WarningNotFoundError,
)

from ..middleware import require_role, validate_token

# Every *NotFoundError -> 404.
_NOT_FOUND_ERRORS = (
    StudentNotFoundError,
    TeacherNotFoundError,
    CohortNotFoundError,
    TopicNotFoundError,
    ProblemNotFoundError,
    ContestNotFoundError,
    SessionNotFoundError,
    MentorshipNotFoundError,
    MentorshipSessionNotFoundError,
    WarningNotFoundError,
)

# Conflicts: resource already exists / already in the requested state /
# operation not valid given the resource's current (but existing) state.
_CONFLICT_ERRORS = (
    StudentAlreadyExistsError,
    TeacherAlreadyExistsError,
    StudentAlreadyInCohortError,
    TeacherAlreadyInCohortError,
    ContestResultsAlreadySubmittedError,
    WarningAlreadyDismissedError,
    CohortArchivedError,
    InvalidStudentStatusTransitionError,
    StudentNotEligibleForPromotionError,
    StudentNotEligibleForGraduationError,
    ContestNotFinishedError,
)


def error_body(status_code: int, error_code: str, message: str) -> dict:
    return {
        "status": status_code,
        "error": error_code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

class BaseAcademicView(APIView):
    def dispatch(self, request, *args, **kwargs):
        from django.http import JsonResponse as DjangoJsonResponse
        try:
            return super().dispatch(request, *args, **kwargs)
        except UnauthorizedAccessError as exc:
            return DjangoJsonResponse(
                error_body(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", str(exc)),
                status=401,
            )

    def handle_domain_exception(self, exc: Exception) -> Response:
        if isinstance(exc, _NOT_FOUND_ERRORS):
            return Response(
                error_body(status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(exc)),
                status=status.HTTP_404_NOT_FOUND,
            )
        if isinstance(exc, _CONFLICT_ERRORS):
            return Response(
                error_body(status.HTTP_409_CONFLICT, "CONFLICT", str(exc)),
                status=status.HTTP_409_CONFLICT,
            )
        if isinstance(exc, UnauthorizedAccessError):
            # Raised by middleware.validate_token for a missing/expired/
            # invalid bearer token. Role-permission failures are handled
            # separately by require_roles() below, which returns a 403
            # Response directly instead of raising — that keeps this
            # exception meaning strictly "who are you" (401), not
            # "you can't do that" (403).
            return Response(
                error_body(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", str(exc)),
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # Not a recognized domain exception — re-raise so DRF's default
        # handling/logging takes over rather than us guessing a status.
        raise exc

    def authenticate(self, request) -> dict:
        """Returns the decoded JWT payload (dict with userId/email/role),
        or raises UnauthorizedAccessError."""
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION", "")
        return validate_token(auth_header)

    @staticmethod
    def require_roles(payload: dict, *allowed_roles: str) -> Response | None:
        """Returns a 403 Response if payload['role'] isn't one of
        allowed_roles, else None. Kept separate from the UnauthorizedAccessError
        raised by authenticate() so a role mismatch always maps to 403,
        never 401 (see handle_domain_exception)."""
        try:
            require_role(payload, *allowed_roles)
        except UnauthorizedAccessError as exc:
            return Response(
                error_body(status.HTTP_403_FORBIDDEN, "FORBIDDEN", str(exc)),
                status=status.HTTP_403_FORBIDDEN,
            )
        return None