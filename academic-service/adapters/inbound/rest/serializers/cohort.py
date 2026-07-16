"""
adapters/inbound/rest/serializers/cohort.py — Academic Service

Mirrors: CohortResponse, CohortListResponse, CreateCohortRequest,
UpdateCohortRequest.
"""
from rest_framework import serializers

from .common import EnumValueField, PageMetaSerializer


class CohortResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    status = EnumValueField()
    intakeWindowOne = serializers.DateField(
        source="intake_window_one", allow_null=True, required=False
    )
    intakeWindowTwo = serializers.DateField(
        source="intake_window_two", allow_null=True, required=False
    )
    startDate = serializers.DateField(source="start_date")
    expectedGraduationDate = serializers.DateField(source="expected_graduation_date")
    studentCapacity = serializers.IntegerField(source="student_capacity")
    enrolledStudentCount = serializers.IntegerField(source="enrolled_student_count")
    teacherCount = serializers.IntegerField(source="teacher_count")
    createdAt = serializers.DateTimeField(source="created_at")


class CohortListResponseSerializer(serializers.Serializer):
    cohorts = CohortResponseSerializer(many=True)
    pagination = PageMetaSerializer(required=False)


class CreateCohortSerializer(serializers.Serializer):
    name = serializers.CharField()
    intakeWindowOne = serializers.DateField(source="intake_window_one", required=False)
    intakeWindowTwo = serializers.DateField(source="intake_window_two", required=False)
    startDate = serializers.DateField(source="start_date")
    expectedGraduationDate = serializers.DateField(source="expected_graduation_date")
    studentCapacity = serializers.IntegerField(source="student_capacity")


class UpdateCohortSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    studentCapacity = serializers.IntegerField(source="student_capacity", required=False)
    expectedGraduationDate = serializers.DateField(
        source="expected_graduation_date", required=False
    )