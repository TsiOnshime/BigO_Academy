"""
adapters/inbound/rest/serializers/warning.py — Academic Service

Mirrors: WarningResponse, WarningListResponse, DismissWarningRequest,
EscalatedStudentListResponse, WarningRulesResponse,
UpdateWarningRulesRequest.

WarningListResponseSerializer matches GetStudentWarningsResult exactly
(student_id, active_warning_count, warnings) — no view-side assembly
needed there.

EscalatedStudentListResponse, however, doesn't match what
ListEscalatedWarningsUseCase returns: the use case returns a flat
list[Warning] (find_escalated), but the spec wants one row per *student*
with studentName/cohortId/warningCount/escalatedAt/warningTypes rolled
up. Grouping warnings by student and joining student/cohort data is a
views.py job; EscalatedStudentSerializer below expects that
already-grouped shape.
"""
from rest_framework import serializers

from .common import EnumValueField


class WarningResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    studentId = serializers.UUIDField(source="student_id")
    type = EnumValueField()
    status = EnumValueField()
    warningNumber = serializers.IntegerField(source="warning_number")
    issuedAt = serializers.DateTimeField(source="issued_at")
    dismissedAt = serializers.DateTimeField(source="dismissed_at", allow_null=True)
    dismissedBy = serializers.UUIDField(source="dismissed_by", allow_null=True)
    dismissalNote = serializers.CharField(source="dismissal_note", allow_null=True)


class WarningListResponseSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    activeWarningCount = serializers.IntegerField(source="active_warning_count")
    warnings = WarningResponseSerializer(many=True)


class DismissWarningSerializer(serializers.Serializer):
    note = serializers.CharField()


class EscalatedStudentSerializer(serializers.Serializer):
    """Nested item inside EscalatedStudentListResponse.students —
    see module docstring for the grouping the view must do first."""

    studentId = serializers.UUIDField(source="student_id")
    studentName = serializers.CharField(source="student_name")
    cohortId = serializers.UUIDField(source="cohort_id")
    warningCount = serializers.IntegerField(source="warning_count")
    escalatedAt = serializers.DateTimeField(source="escalated_at")
    warningTypes = serializers.ListField(child=EnumValueField(), source="warning_types")


class EscalatedStudentListResponseSerializer(serializers.Serializer):
    students = EscalatedStudentSerializer(many=True)


class WarningRulesResponseSerializer(serializers.Serializer):
    minAttendancePercentage = serializers.FloatField(source="min_attendance_percentage")
    minContestParticipationPercentage = serializers.FloatField(
        source="min_contest_participation_percentage"
    )
    maxWarningsBeforeEscalation = serializers.IntegerField(
        source="max_warnings_before_escalation"
    )
    # view-supplied: WarningRules (application/ports/outbound/
    # warning_rules_repository.py) has no updatedAt field — only the ORM
    # row does. The view can attach it from the repo if needed, or omit.
    updatedAt = serializers.DateTimeField(
        source="updated_at", required=False, allow_null=True
    )


class UpdateWarningRulesSerializer(serializers.Serializer):
    minAttendancePercentage = serializers.FloatField(
        source="min_attendance_percentage", required=False
    )
    minContestParticipationPercentage = serializers.FloatField(
        source="min_contest_participation_percentage", required=False
    )
    maxWarningsBeforeEscalation = serializers.IntegerField(
        source="max_warnings_before_escalation", required=False
    )