"""
adapters/inbound/rest/views/cohort_views.py — Academic Service

POST/GET  /cohorts/                                  CohortListCreateView
GET/PATCH /cohorts/<cohort_id>/                      CohortDetailView
POST      /cohorts/<cohort_id>/archive/              ArchiveCohortView
POST      /cohorts/<cohort_id>/students/             AssignStudentToCohortView
POST      /cohorts/<cohort_id>/teachers/             AssignTeacherToCohortView
DELETE    /cohorts/<cohort_id>/teachers/<teacher_id>/ UnassignTeacherFromCohortView
GET       /cohorts/<cohort_id>/attendance/           GetCohortAttendanceView

GET+POST on `/cohorts/` and GET+PATCH on `/cohorts/<id>/` are combined
into single classes — see student_views.py's module docstring for why
(Django's URL resolver dispatches on pattern, not verb). All other
routes below have a unique path (no verb collision), so each stays its
own view class.

CohortResponseSerializer needs no view-supplied fields — every field is
already on domain.Cohort.

GetCohortAttendanceView resolves the documented CohortAttendanceResponse
gap (studentSummaries / overallAttendancePercentage aren't produced by
any use case — see serializers/attendance.py docstring) the same way
attendance_views.py does: studentSummaries comes from the cohort roster
via ListStudentsUseCase using the already-denormalized
Student.attendance_percentage field, and overallAttendancePercentage is
the mean of each returned session's own attendance_percentage().
"""
from rest_framework import status
from rest_framework.response import Response

from application.use_cases.attendance.get_cohort_attendance import (
    GetCohortAttendanceCommand,
)
from application.use_cases.cohort.archive_cohort import ArchiveCohortCommand
from application.use_cases.cohort.assign_student_to_cohort import (
    AssignStudentToCohortCommand,
)
from application.use_cases.cohort.assign_teacher_to_cohort import (
    AssignTeacherToCohortCommand,
)
from application.use_cases.cohort.create_cohort import CreateCohortCommand
from application.use_cases.cohort.get_cohort import GetCohortCommand
from application.use_cases.cohort.list_cohorts import ListCohortsCommand
from application.use_cases.cohort.unassign_teacher_from_cohort import (
    UnassignTeacherFromCohortCommand,
)
from application.use_cases.cohort.update_cohort import UpdateCohortCommand
from application.use_cases.student.list_students import ListStudentsCommand
from domain.enums import CohortStatus
from infrastructure.config.dependencies import (
    get_archive_cohort_use_case,
    get_assign_student_to_cohort_use_case,
    get_assign_teacher_to_cohort_use_case,
    get_create_cohort_use_case,
    get_get_cohort_attendance_use_case,
    get_get_cohort_use_case,
    get_list_cohorts_use_case,
    get_list_students_use_case,
    get_unassign_teacher_from_cohort_use_case,
    get_update_cohort_use_case,
)

from ..serializers import (
    AssignStudentSerializer,
    AssignTeacherSerializer,
    CohortAttendanceResponseSerializer,
    CohortListResponseSerializer,
    CohortResponseSerializer,
    CreateCohortSerializer,
    UpdateCohortSerializer,
)
from .base import BaseAcademicView


class CohortListCreateView(BaseAcademicView):

    def post(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = CreateCohortSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_create_cohort_use_case()
            result = use_case.execute(
                CreateCohortCommand(
                    name=data["name"],
                    start_date=data["start_date"],
                    expected_graduation_date=data["expected_graduation_date"],
                    student_capacity=data["student_capacity"],
                    intake_window_one=data.get("intake_window_one"),
                    intake_window_two=data.get("intake_window_two"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            CohortResponseSerializer(result.cohort).data,
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        status_param = request.query_params.get("status")

        try:
            use_case = get_list_cohorts_use_case()
            cohorts = use_case.execute(
                ListCohortsCommand(
                    status=CohortStatus(status_param) if status_param else None
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(CohortListResponseSerializer({"cohorts": cohorts}).data)


class CohortDetailView(BaseAcademicView):

    def get(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            use_case = get_get_cohort_use_case()
            cohort = use_case.execute(GetCohortCommand(cohort_id=cohort_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(CohortResponseSerializer(cohort).data)

    def patch(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = UpdateCohortSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_cohort_use_case()
            cohort = use_case.execute(
                UpdateCohortCommand(
                    cohort_id=cohort_id,
                    name=data.get("name"),
                    student_capacity=data.get("student_capacity"),
                    expected_graduation_date=data.get("expected_graduation_date"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(CohortResponseSerializer(cohort).data)


class ArchiveCohortView(BaseAcademicView):
    def post(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        try:
            use_case = get_archive_cohort_use_case()
            cohort = use_case.execute(ArchiveCohortCommand(cohort_id=cohort_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(CohortResponseSerializer(cohort).data)


class AssignStudentToCohortView(BaseAcademicView):
    def post(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = AssignStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_assign_student_to_cohort_use_case()
            use_case.execute(
                AssignStudentToCohortCommand(
                    cohort_id=cohort_id, student_id=data["student_id"]
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignTeacherToCohortView(BaseAcademicView):
    def post(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = AssignTeacherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_assign_teacher_to_cohort_use_case()
            use_case.execute(
                AssignTeacherToCohortCommand(
                    cohort_id=cohort_id, teacher_id=data["teacher_id"]
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class UnassignTeacherFromCohortView(BaseAcademicView):
    def delete(self, request, cohort_id, teacher_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        try:
            use_case = get_unassign_teacher_from_cohort_use_case()
            use_case.execute(
                UnassignTeacherFromCohortCommand(
                    cohort_id=cohort_id, teacher_id=teacher_id
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class GetCohortAttendanceView(BaseAcademicView):
    def get(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        from datetime import date

        from_date_param = request.query_params.get("fromDate")
        to_date_param = request.query_params.get("toDate")
        from_date = date.fromisoformat(from_date_param) if from_date_param else None
        to_date = date.fromisoformat(to_date_param) if to_date_param else None

        try:
            sessions = get_get_cohort_attendance_use_case().execute(
                GetCohortAttendanceCommand(
                    cohort_id=cohort_id, from_date=from_date, to_date=to_date
                )
            )
            roster = get_list_students_use_case().execute(
                ListStudentsCommand(cohort_id=cohort_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        if sessions:
            overall_percentage = round(
                sum(s.attendance_percentage() for s in sessions) / len(sessions), 2
            )
        else:
            overall_percentage = 0.0

        student_summaries = [
            {
                "student_id": s.id,
                "student_name": s.full_name,
                "attendance_percentage": s.attendance_percentage,
            }
            for s in roster
        ]

        body = {
            "cohort_id": cohort_id,
            "total_sessions": len(sessions),
            "overall_attendance_percentage": overall_percentage,
            "student_summaries": student_summaries,
        }
        return Response(CohortAttendanceResponseSerializer(body).data)