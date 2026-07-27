"""
adapters/inbound/rest/views/mentorship_views.py — Academic Service

POST/GET  /mentorship-sessions/                 MentorshipSessionListCreateView
GET/PATCH /mentorship-sessions/<session_id>/    MentorshipSessionDetailView

GET+POST on `/mentorship-sessions/` and GET+PATCH on
`/mentorship-sessions/<id>/` are combined into single classes — see
student_views.py's module docstring for why (Django's URL resolver
dispatches on pattern, not verb).

MentorshipSessionResponse needs view-supplied `teacherName` and
`studentName` (see serializers/mentorship.py docstring) — domain.
MentorshipSession only carries the ids. Every view below resolves both
names via GetTeacherUseCase / GetStudentUseCase, batching lookups for
the list endpoint to avoid N+1 calls per distinct id.
"""
from dataclasses import asdict
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response

from application.use_cases.mentorship.get_mentorship_session import (
    GetMentorshipSessionCommand,
)
from application.use_cases.mentorship.list_mentorship_sessions import (
    ListMentorshipSessionsCommand,
)
from application.use_cases.mentorship.schedule_mentorship import (
    ScheduleMentorshipCommand,
)
from application.use_cases.mentorship.update_mentorship_session import (
    UpdateMentorshipSessionCommand,
)
from application.use_cases.student.get_student import GetStudentCommand
from application.use_cases.teacher.get_teacher import GetTeacherCommand
from domain.enums import MentorshipSessionStatus
from infrastructure.config.dependencies import (
    get_get_mentorship_session_use_case,
    get_get_student_use_case,
    get_get_teacher_use_case,
    get_list_mentorship_sessions_use_case,
    get_schedule_mentorship_use_case,
    get_update_mentorship_session_use_case,
)

from ..serializers import (
    CreateMentorshipSessionSerializer,
    MentorshipSessionListResponseSerializer,
    MentorshipSessionResponseSerializer,
    UpdateMentorshipSessionSerializer,
)
from .base import BaseAcademicView


def _session_to_dict(session, teacher_name=None, student_name=None) -> dict:
    data = asdict(session)
    data["teacher_name"] = teacher_name
    data["student_name"] = student_name
    return data


class MentorshipSessionListCreateView(BaseAcademicView):

    def post(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = CreateMentorshipSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_schedule_mentorship_use_case()
            session = use_case.execute(
                ScheduleMentorshipCommand(
                    teacher_id=data["teacher_id"],
                    student_id=data["student_id"],
                    scheduled_at=data["scheduled_at"],
                )
            )
            teacher = get_get_teacher_use_case().execute(
                GetTeacherCommand(teacher_id=session.teacher_id)
            )
            student = get_get_student_use_case().execute(
                GetStudentCommand(student_id=session.student_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _session_to_dict(session, teacher.full_name, student.full_name)
        return Response(
            MentorshipSessionResponseSerializer(body).data,
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        student_id_param = request.query_params.get("studentId")
        teacher_id_param = request.query_params.get("teacherId")

        try:
            use_case = get_list_mentorship_sessions_use_case()
            sessions = use_case.execute(
                ListMentorshipSessionsCommand(
                    student_id=UUID(student_id_param) if student_id_param else None,
                    teacher_id=UUID(teacher_id_param) if teacher_id_param else None,
                )
            )

            teacher_names = {}
            student_names = {}
            for tid in {s.teacher_id for s in sessions}:
                teacher_names[tid] = get_get_teacher_use_case().execute(
                    GetTeacherCommand(teacher_id=tid)
                ).full_name
            for sid in {s.student_id for s in sessions}:
                student_names[sid] = get_get_student_use_case().execute(
                    GetStudentCommand(student_id=sid)
                ).full_name
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = {
            "sessions": [
                _session_to_dict(
                    s, teacher_names.get(s.teacher_id), student_names.get(s.student_id)
                )
                for s in sessions
            ]
        }
        return Response(MentorshipSessionListResponseSerializer(body).data)


class MentorshipSessionDetailView(BaseAcademicView):

    def get(self, request, session_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            session = get_get_mentorship_session_use_case().execute(
                GetMentorshipSessionCommand(session_id=session_id)
            )
            teacher = get_get_teacher_use_case().execute(
                GetTeacherCommand(teacher_id=session.teacher_id)
            )
            student = get_get_student_use_case().execute(
                GetStudentCommand(student_id=session.student_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _session_to_dict(session, teacher.full_name, student.full_name)
        return Response(MentorshipSessionResponseSerializer(body).data)

    def patch(self, request, session_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = UpdateMentorshipSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_mentorship_session_use_case()
            session = use_case.execute(
                UpdateMentorshipSessionCommand(
                    session_id=session_id,
                    scheduled_at=data.get("scheduled_at"),
                    status=MentorshipSessionStatus(data["status"])
                    if data.get("status")
                    else None,
                    notes=data.get("notes"),
                )
            )
            teacher = get_get_teacher_use_case().execute(
                GetTeacherCommand(teacher_id=session.teacher_id)
            )
            student = get_get_student_use_case().execute(
                GetStudentCommand(student_id=session.student_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _session_to_dict(session, teacher.full_name, student.full_name)
        return Response(MentorshipSessionResponseSerializer(body).data)