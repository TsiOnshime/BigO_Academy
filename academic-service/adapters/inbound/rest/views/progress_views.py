"""
adapters/inbound/rest/views/progress_views.py — Academic Service

PATCH /students/<student_id>/progress/<problem_id>/  UpdateProblemProgressView
GET   /students/<student_id>/progress/                GetStudentProgressView

These two routes don't collide (the trailing path segment differs), so
each stays its own view class — unlike student/teacher/cohort/etc.,
there's no GET+POST or GET+PATCH sharing one exact URL here.

ProblemProgressResponse needs a view-supplied `problemTitle` (see
serializers/progress.py docstring) — domain.ProblemProgress has no such
field. There is no "get problem" use case, so per the serializer
docstring's own guidance this is resolved via the curriculum repository
accessor (infrastructure.config.dependencies.get_curriculum_repository),
the same read-only, no-business-rule lookup pattern used for
StudentResponse.cohortName elsewhere.

Also per that same docstring: the OpenAPI spec nests progress by topic,
but GetStudentProgressUseCase returns a flat list — this view renders
the flat shape (ProgressSheetResponseSerializer), matching what the use
case actually returns, rather than inventing topic-grouping logic that
isn't backed by any use case.
"""
from dataclasses import asdict
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response

from application.use_cases.progress.get_student_progress import (
    GetStudentProgressCommand,
)
from application.use_cases.progress.update_problem_progress import (
    UpdateProblemProgressCommand,
)
from infrastructure.config.dependencies import (
    get_curriculum_repository,
    get_get_student_progress_use_case,
    get_update_problem_progress_use_case,
)

from ..serializers import (
    ProblemProgressResponseSerializer,
    ProgressSheetResponseSerializer,
    UpdateProgressSerializer,
)
from .base import BaseAcademicView


def _problem_title_for(problem_id) -> str | None:
    problem = get_curriculum_repository().find_problem_by_id(problem_id)
    return problem.title if problem is not None else None


class UpdateProblemProgressView(BaseAcademicView):
    def patch(self, request, student_id, problem_id):
        payload = self.authenticate(request)
        # A student may only update their own progress record; teachers/
        # admins may update any student's. Fine-grained ownership
        # checking (comparing payload's userId to the student's
        # user_id) is intentionally left out here — see module-level
        # note in warning_views.py for the same trade-off discussion.
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        serializer = UpdateProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_problem_progress_use_case()
            progress = use_case.execute(
                UpdateProblemProgressCommand(
                    student_id=student_id,
                    problem_id=problem_id,
                    solved=data["solved"],
                    attempt_count=data.get("attempt_count"),
                    solve_time_minutes=data.get("solve_time_minutes"),
                    verified_by_teacher=data.get("verified_by_teacher"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = asdict(progress)
        body["problem_title"] = _problem_title_for(progress.problem_id)
        return Response(ProblemProgressResponseSerializer(body).data)


class GetStudentProgressView(BaseAcademicView):
    def get(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        topic_id_param = request.query_params.get("topicId")

        try:
            use_case = get_get_student_progress_use_case()
            result = use_case.execute(
                GetStudentProgressCommand(
                    student_id=student_id,
                    topic_id=UUID(topic_id_param) if topic_id_param else None,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        progress_items = []
        for p in result.progress:
            item = asdict(p)
            item["problem_title"] = _problem_title_for(p.problem_id)
            progress_items.append(item)

        body = {
            "student_id": result.student_id,
            "total_problems": result.total_problems,
            "solved_count": result.solved_count,
            "completion_percentage": result.completion_percentage,
            "progress": progress_items,
        }
        return Response(ProgressSheetResponseSerializer(body).data)