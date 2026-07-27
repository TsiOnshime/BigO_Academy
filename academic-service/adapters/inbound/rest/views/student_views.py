"""
adapters/inbound/rest/views/student_views.py — Academic Service

POST/GET  /students/                       StudentListCreateView
GET/PATCH /students/<student_id>/          StudentDetailView
POST      /students/<student_id>/promote/  PromoteStudentView

Views sharing the same URL (GET+POST on `/students/`, GET+PATCH on
`/students/<id>/`) are single classes with both HTTP methods defined —
Django's URL resolver dispatches on the *pattern* only, not the verb, so
two separate path() entries with an identical route would always match
the first one regardless of method.

StudentResponseSerializer needs a view-supplied `cohort_name` (domain.
Student has no such field — see serializers/student.py docstring).
`_student_to_dict` looks the cohort name up via the cohort repository
accessor and folds it into a plain dict (DRF's Serializer supports
Mapping instances via get_attribute, so a dict with snake_case keys
matching each field's `source` renders exactly like the dataclass would).
"""
from dataclasses import asdict
from datetime import date
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response

from application.use_cases.student.create_student import CreateStudentCommand
from application.use_cases.student.get_student import GetStudentCommand
from application.use_cases.student.graduate_student import GraduateStudentCommand
from application.use_cases.student.list_students import ListStudentsCommand
from application.use_cases.student.promote_student import PromoteStudentCommand
from application.use_cases.student.update_student import UpdateStudentCommand
from application.use_cases.student.update_student_status import (
    UpdateStudentStatusCommand,
)
from domain.enums import StudentStatus
from infrastructure.config.dependencies import (
    get_cohort_repository,
    get_create_student_use_case,
    get_get_student_use_case,
    get_graduate_student_use_case,
    get_list_students_use_case,
    get_promote_student_use_case,
    get_update_student_status_use_case,
    get_update_student_use_case,
)

from ..serializers import (
    CreateStudentSerializer,
    StudentListResponseSerializer,
    StudentResponseSerializer,
    UpdateStudentSerializer,
    UpdateStudentStatusSerializer,
)
from .base import BaseAcademicView


def _student_to_dict(student, cohort_name=None) -> dict:
    data = asdict(student)
    data["cohort_name"] = cohort_name
    return data


def _cohort_name_for(cohort_id) -> str | None:
    if cohort_id is None:
        return None
    cohort = get_cohort_repository().find_by_id(cohort_id)
    return cohort.name if cohort is not None else None


class StudentListCreateView(BaseAcademicView):

    def post(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = CreateStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_create_student_use_case()
            result = use_case.execute(
                CreateStudentCommand(
                    user_id=data["user_id"],
                    full_name=data["full_name"],
                    email=data["email"],
                    cohort_id=data["cohort_id"],
                    # CreateStudentCommand.joined_at has no default —
                    # default to today when the caller omits it.
                    joined_at=data.get("joined_at") or date.today(),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        student = result.student
        body = _student_to_dict(student, _cohort_name_for(student.cohort_id))
        return Response(
            StudentResponseSerializer(body).data, status=status.HTTP_201_CREATED
        )

    def get(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        cohort_id_param = request.query_params.get("cohortId")
        status_param = request.query_params.get("status")

        try:
            use_case = get_list_students_use_case()
            students = use_case.execute(
                ListStudentsCommand(
                    cohort_id=UUID(cohort_id_param) if cohort_id_param else None,
                    status=StudentStatus(status_param) if status_param else None,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        # Batch cohort-name lookups: one find_by_id per distinct cohort
        # instead of per student.
        cohort_names = {}
        for cid in {s.cohort_id for s in students if s.cohort_id is not None}:
            cohort_names[cid] = _cohort_name_for(cid)

        body = {
            "students": [
                _student_to_dict(s, cohort_names.get(s.cohort_id)) for s in students
            ]
        }
        return Response(StudentListResponseSerializer(body).data)


class StudentDetailView(BaseAcademicView):

    def get(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            use_case = get_get_student_use_case()
            student = use_case.execute(GetStudentCommand(student_id=student_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _student_to_dict(student, _cohort_name_for(student.cohort_id))
        return Response(StudentResponseSerializer(body).data)

    def patch(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = UpdateStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_student_use_case()
            student = use_case.execute(
                UpdateStudentCommand(
                    student_id=student_id,
                    full_name=data.get("full_name"),
                    email=data.get("email"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _student_to_dict(student, _cohort_name_for(student.cohort_id))
        return Response(StudentResponseSerializer(body).data)


class PromoteStudentView(BaseAcademicView):
    def post(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        try:
            use_case = get_promote_student_use_case()
            student = use_case.execute(PromoteStudentCommand(student_id=student_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _student_to_dict(student, _cohort_name_for(student.cohort_id))
        return Response(StudentResponseSerializer(body).data)


class UpdateStudentStatusView(BaseAcademicView):
    def patch(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = UpdateStudentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_student_status_use_case()
            student = use_case.execute(
                UpdateStudentStatusCommand(
                    student_id=student_id,
                    new_status=StudentStatus(data["status"]),
                    reason=data.get("reason"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _student_to_dict(student, _cohort_name_for(student.cohort_id))
        return Response(StudentResponseSerializer(body).data)


class GraduateStudentView(BaseAcademicView):
    def post(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        try:
            use_case = get_graduate_student_use_case()
            student = use_case.execute(GraduateStudentCommand(student_id=student_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = _student_to_dict(student, _cohort_name_for(student.cohort_id))
        return Response(StudentResponseSerializer(body).data)