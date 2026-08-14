"""
adapters/inbound/rest/serializers/student.py — Academic Service

Mirrors: StudentResponse, StudentListResponse, CreateStudentRequest,
UpdateStudentRequest, UpdateStudentStatusRequest, AssignStudentRequest.
"""
from rest_framework import serializers

from domain.enums import StudentStatus

from .common import EnumValueField, PageMetaSerializer


class StudentResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    fullName = serializers.CharField(source="full_name")
    email = serializers.EmailField()
    status = EnumValueField()
    yearPhase = EnumValueField(source="year_phase")
    cohortId = serializers.UUIDField(source="cohort_id", allow_null=True)
    # view-supplied: not on domain.Student — the view looks up the cohort
    # (if any) and adds `cohort_name` before serializing.
    cohortName = serializers.CharField(source="cohort_name", allow_null=True, required=False)
    codeforcesHandle = serializers.CharField(source="codeforces_handle", allow_null=True, required=False)
    codeforcesRating = serializers.IntegerField(source="codeforces_rating", allow_null=True, required=False, default=0)
    codeforcesRank = serializers.CharField(source="codeforces_rank", allow_null=True, required=False, default="unrated")
    codeforcesMaxRating = serializers.IntegerField(source="codeforces_max_rating", allow_null=True, required=False, default=0)
    solvedCount = serializers.IntegerField(source="solved_count", required=False, default=0)
    totalProblems = serializers.IntegerField(source="total_problems", required=False, default=0)
    assignedTeacherId = serializers.UUIDField(source="assigned_teacher_id", allow_null=True)
    attendancePercentage = serializers.FloatField(source="attendance_percentage")
    activeWarningCount = serializers.IntegerField(source="active_warning_count")
    joinedAt = serializers.DateField(source="joined_at")
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")


class StudentListResponseSerializer(serializers.Serializer):
    students = StudentResponseSerializer(many=True)
    pagination = PageMetaSerializer(required=False)


class CreateStudentSerializer(serializers.Serializer):
    userId = serializers.UUIDField(source="user_id")
    fullName = serializers.CharField(source="full_name")
    email = serializers.EmailField()
    cohortId = serializers.UUIDField(source="cohort_id")
    codeforcesHandle = serializers.CharField(source="codeforces_handle", required=False, allow_blank=True, allow_null=True)
    joinedAt = serializers.DateField(source="joined_at", required=False)

class UpdateStudentSerializer(serializers.Serializer):
    fullName = serializers.CharField(source="full_name", required=False)
    email = serializers.EmailField(required=False)
    codeforcesHandle = serializers.CharField(source="codeforces_handle", required=False, allow_blank=True, allow_null=True)


class UpdateStudentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s.value for s in StudentStatus])
    reason = serializers.CharField(required=False, allow_blank=True)


class AssignStudentSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")