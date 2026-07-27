"""
adapters/inbound/rest/views/warning_views.py — Academic Service

GET       /students/<student_id>/warnings/  GetStudentWarningsView
POST      /warnings/<warning_id>/dismiss/   DismissWarningView
GET       /warnings/escalated/              ListEscalatedWarningsView
GET/PATCH /warnings/rules/                  WarningRulesView

GET+PATCH on `/warnings/rules/` are combined into a single class — see
student_views.py's module docstring for why (Django's URL resolver
dispatches on pattern, not verb).

Known gap (not silently worked around): EscalatedStudentListResponse
needs one row per *student* (studentName, cohortId, warningCount,
escalatedAt, warningTypes rolled up), but ListEscalatedWarningsUseCase
returns a flat list[Warning] (see serializers/warning.py docstring).
Grouping by student and joining cohort/name data requires student.
cohort_id and student.full_name — available via GetStudentUseCase — but
warning.escalated_at and a per-student "warningTypes" set aren't derived
from any single field on Warning in an unambiguous way beyond "every
warning this student currently has on file"; this view groups by
student_id, uses each group's most recent issued_at as escalatedAt, and
lists the distinct warning types across the group. This is a view-level
judgment call flagged here rather than treated as an exact spec match.
"""
from collections import defaultdict
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response

from application.use_cases.student.get_student import GetStudentCommand
from application.use_cases.warning.dismiss_warning import DismissWarningCommand
from application.use_cases.warning.get_student_warnings import (
    GetStudentWarningsCommand,
)
from application.use_cases.warning.list_escalated_warnings import (
    ListEscalatedWarningsCommand,
)
from application.use_cases.warning.update_warning_rules import (
    UpdateWarningRulesCommand,
)
from infrastructure.config.dependencies import (
    get_dismiss_warning_use_case,
    get_get_student_use_case,
    get_get_student_warnings_use_case,
    get_get_warning_rules_use_case,
    get_list_escalated_warnings_use_case,
    get_update_warning_rules_use_case,
)

from ..serializers import (
    DismissWarningSerializer,
    EscalatedStudentListResponseSerializer,
    UpdateWarningRulesSerializer,
    WarningListResponseSerializer,
    WarningResponseSerializer,
    WarningRulesResponseSerializer,
)
from .base import BaseAcademicView


class GetStudentWarningsView(BaseAcademicView):
    def get(self, request, student_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            use_case = get_get_student_warnings_use_case()
            result = use_case.execute(
                GetStudentWarningsCommand(student_id=student_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(WarningListResponseSerializer(result).data)


class DismissWarningView(BaseAcademicView):
    def post(self, request, warning_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = DismissWarningSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_dismiss_warning_use_case()
            warning = use_case.execute(
                DismissWarningCommand(
                    warning_id=warning_id,
                    dismissed_by=UUID(payload["user_id"]),
                    note=data["note"],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(WarningResponseSerializer(warning).data)


class ListEscalatedWarningsView(BaseAcademicView):
    def get(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        cohort_id_param = request.query_params.get("cohortId")

        try:
            warnings = get_list_escalated_warnings_use_case().execute(
                ListEscalatedWarningsCommand(
                    cohort_id=UUID(cohort_id_param) if cohort_id_param else None
                )
            )

            # See module docstring for the grouping rationale.
            by_student = defaultdict(list)
            for w in warnings:
                by_student[w.student_id].append(w)

            students_out = []
            for student_id, group in by_student.items():
                student = get_get_student_use_case().execute(
                    GetStudentCommand(student_id=student_id)
                )
                latest = max(group, key=lambda w: w.issued_at)
                students_out.append(
                    {
                        "student_id": student_id,
                        "student_name": student.full_name,
                        "cohort_id": student.cohort_id,
                        "warning_count": len(group),
                        "escalated_at": latest.issued_at,
                        "warning_types": [w.type for w in group],
                    }
                )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            EscalatedStudentListResponseSerializer({"students": students_out}).data
        )


class WarningRulesView(BaseAcademicView):

    def get(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        try:
            rules = get_get_warning_rules_use_case().execute()
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(WarningRulesResponseSerializer(rules).data)

    def patch(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = UpdateWarningRulesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_warning_rules_use_case()
            rules = use_case.execute(
                UpdateWarningRulesCommand(
                    min_attendance_percentage=data.get("min_attendance_percentage"),
                    min_contest_participation_percentage=data.get(
                        "min_contest_participation_percentage"
                    ),
                    max_warnings_before_escalation=data.get(
                        "max_warnings_before_escalation"
                    ),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(WarningRulesResponseSerializer(rules).data)