"""
adapters/inbound/rest/serializers/attendance.py — Academic Service

Mirrors: SubmitAttendanceRequest, AttendanceRecord, EditAttendanceRequest,
AttendanceSessionResponse, StudentAttendanceResponse,
AttendanceHistoryEntry, CohortAttendanceResponse.

Known gap (flagging, not silently working around): AttendanceHistoryEntry
requires `sessionDate` per record, but domain.AttendanceRecord (and the
DjangoAttendanceRepository.find_student_attendance implementation built
in the previous step) only carries student_id/status/note — no date. The
date lives on ClassSession, one level up, and the domain AttendanceRecord
dataclass has no session reference. Rendering AttendanceHistoryEntry
correctly needs either a domain-layer change (add a date, or return
paired (session, record) tuples) or the view doing extra correlation
work — this is a domain-modeling gap, not something serializers.py can
paper over cleanly. AttendanceHistoryEntrySerializer is defined per spec
below; it expects `session_date` to be present on whatever the view hands
it.
"""
from rest_framework import serializers

from domain.enums import AttendanceStatus

from .common import EnumValueField


class AttendanceRecordSerializer(serializers.Serializer):
    """Shared shape for both request input (SubmitAttendanceRequest.records,
    EditAttendanceRequest.records) and as a component of
    AttendanceSessionResponse.records."""

    studentId = serializers.UUIDField(source="student_id")
    status = EnumValueField(required=False)  # response mode
    note = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def to_internal_value(self, data):
        # Request mode: validate `status` as one of the allowed enum
        # strings (EnumValueField is response-only/read-only).
        internal = super().to_internal_value(
            {k: v for k, v in data.items() if k != "status"}
        )
        status_value = data.get("status")
        if status_value not in [s.value for s in AttendanceStatus]:
            raise serializers.ValidationError(
                {"status": f"'{status_value}' is not a valid AttendanceStatus"}
            )
        internal["status"] = status_value
        return internal


class SubmitAttendanceSerializer(serializers.Serializer):
    cohortId = serializers.UUIDField(source="cohort_id")
    sessionDate = serializers.DateField(source="session_date")
    records = AttendanceRecordSerializer(many=True)


class EditAttendanceSerializer(serializers.Serializer):
    records = AttendanceRecordSerializer(many=True)


class AttendanceSessionResponseSerializer(serializers.Serializer):
    sessionId = serializers.UUIDField(source="id")
    cohortId = serializers.UUIDField(source="cohort_id")
    sessionDate = serializers.DateField(source="session_date")
    totalStudents = serializers.IntegerField(source="total_students")
    presentCount = serializers.IntegerField(source="present_count")
    absentCount = serializers.IntegerField(source="absent_count")
    excusedCount = serializers.IntegerField(source="excused_count")
    records = AttendanceRecordSerializer(many=True)


class AttendanceHistoryEntrySerializer(serializers.Serializer):
    # view-supplied: see module docstring — domain.AttendanceRecord has no
    # date field, so `session_date` must be attached by the view.
    sessionDate = serializers.DateField(source="session_date")
    status = EnumValueField()
    note = serializers.CharField(allow_null=True, required=False)


class StudentAttendanceResponseSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    attendancePercentage = serializers.FloatField(source="attendance_percentage")
    totalSessions = serializers.IntegerField(source="total_sessions")
    presentCount = serializers.IntegerField(source="present_count")
    absentCount = serializers.IntegerField(source="absent_count")
    excusedCount = serializers.IntegerField(source="excused_count")
    history = AttendanceHistoryEntrySerializer(many=True)


class StudentAttendanceSummarySerializer(serializers.Serializer):
    """Nested item inside CohortAttendanceResponse.studentSummaries."""

    studentId = serializers.UUIDField(source="student_id")
    # view-supplied: joined from student_repository.
    studentName = serializers.CharField(source="student_name")
    attendancePercentage = serializers.FloatField(source="attendance_percentage")


class CohortAttendanceResponseSerializer(serializers.Serializer):
    cohortId = serializers.UUIDField(source="cohort_id")
    totalSessions = serializers.IntegerField(source="total_sessions")
    overallAttendancePercentage = serializers.FloatField(
        source="overall_attendance_percentage"
    )
    studentSummaries = StudentAttendanceSummarySerializer(
        many=True, source="student_summaries"
    )