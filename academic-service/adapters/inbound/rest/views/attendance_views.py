"""
adapters/inbound/rest/views/attendance_views.py — Academic Service

POST      /attendance/sessions/                 SubmitAttendanceView
GET/PATCH /attendance/sessions/<session_id>/    SessionAttendanceDetailView
GET       /students/<student_id>/attendance/    GetStudentAttendanceView

Note: GetCohortAttendanceView lives in cohort_views.py instead of here,
since its URL (`/cohorts/<cohort_id>/attendance/`) is cohort-scoped and
sits alongside the rest of the cohort routes.

GET+PATCH on `/attendance/sessions/<id>/` are combined into a single
class — see student_views.py's module docstring for why (Django's URL
resolver dispatches on pattern, not verb).

GetStudentAttendanceView resolves a documented gap from
serializers/attendance.py: AttendanceHistoryEntry needs `sessionDate`
per record, but GetStudentAttendanceUseCase's `history` is a flat
list[AttendanceRecord] with no date (domain.AttendanceRecord carries no
session reference — see adapters/outbound/persistence/attendance_repo.py's
own docstring on this). Rather than changing the domain/port contract,
this view re-derives session dates by calling GetCohortAttendanceUseCase
for the student's own cohort over the same date range and matching each
session's per-student record back to the student — using only existing
use cases, no direct repository/ORM access.
"""
from datetime import date

from rest_framework import status
from rest_framework.response import Response

from application.use_cases.attendance.edit_attendance import (
    AttendanceEditInput,
    EditAttendanceCommand,
)
from application.use_cases.attendance.get_cohort_attendance import (
    GetCohortAttendanceCommand,
)
from application.use_cases.attendance.get_session_attendance import (
    GetSessionAttendanceCommand,
)
from application.use_cases.attendance.get_student_attendance import (
    GetStudentAttendanceCommand,
)
from application.use_cases.attendance.submit_attendance import (
    AttendanceRecordInput,
    SubmitAttendanceCommand,
)
from application.use_cases.student.get_student import GetStudentCommand
from domain.enums import AttendanceStatus
from infrastructure.config.dependencies import (
    get_edit_attendance_use_case,
    get_get_cohort_attendance_use_case,
    get_get_session_attendance_use_case,
    get_get_student_attendance_use_case,
    get_get_student_use_case,
    get_submit_attendance_use_case,
)

from ..serializers import (
    AttendanceSessionResponseSerializer,
    EditAttendanceSerializer,
    StudentAttendanceResponseSerializer,
    SubmitAttendanceSerializer,
)
from .base import BaseAcademicView


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class SubmitAttendanceView(BaseAcademicView):
    def post(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = SubmitAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_submit_attendance_use_case()
            session = use_case.execute(
                SubmitAttendanceCommand(
                    cohort_id=data["cohort_id"],
                    session_date=data["session_date"],
                    records=[
                        AttendanceRecordInput(
                            student_id=r["student_id"],
                            status=AttendanceStatus(r["status"]),
                            note=r.get("note"),
                        )
                        for r in data["records"]
                    ],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            AttendanceSessionResponseSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


class SessionAttendanceDetailView(BaseAcademicView):

    def get(self, request, session_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            use_case = get_get_session_attendance_use_case()
            session = use_case.execute(
                GetSessionAttendanceCommand(session_id=session_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AttendanceSessionResponseSerializer(session).data)

    def patch(self, request, session_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = EditAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_edit_attendance_use_case()
            session = use_case.execute(
                EditAttendanceCommand(
                    session_id=session_id,
                    records=[
                        AttendanceEditInput(
                            student_id=r["student_id"],
                            status=AttendanceStatus(r["status"]),
                            note=r.get("note"),
                        )
                        for r in data["records"]
                    ],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(AttendanceSessionResponseSerializer(session).data)


class GetStudentAttendanceView(BaseAcademicView):
    def get(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        from_date = _parse_date(request.query_params.get("fromDate"))
        to_date = _parse_date(request.query_params.get("toDate"))

        try:
            student = get_get_student_use_case().execute(
                GetStudentCommand(student_id=student_id)
            )
            result = get_get_student_attendance_use_case().execute(
                GetStudentAttendanceCommand(
                    student_id=student_id, from_date=from_date, to_date=to_date
                )
            )

            # See module docstring: re-derive session_date per history
            # entry via the student's own cohort's sessions.
            history_entries = []
            if student.cohort_id is not None:
                sessions = get_get_cohort_attendance_use_case().execute(
                    GetCohortAttendanceCommand(
                        cohort_id=student.cohort_id,
                        from_date=from_date,
                        to_date=to_date,
                    )
                )
                for session in sessions:
                    for record in session.records:
                        if record.student_id == student_id:
                            history_entries.append(
                                {
                                    "session_date": session.session_date,
                                    "status": record.status,
                                    "note": record.note,
                                }
                            )
                history_entries.sort(key=lambda e: e["session_date"])
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = {
            "student_id": result.student_id,
            "attendance_percentage": result.attendance_percentage,
            "total_sessions": result.total_sessions,
            "present_count": result.present_count,
            "absent_count": result.absent_count,
            "excused_count": result.excused_count,
            "history": history_entries,
        }
        return Response(StudentAttendanceResponseSerializer(body).data)