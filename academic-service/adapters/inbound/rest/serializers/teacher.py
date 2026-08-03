"""
adapters/inbound/rest/serializers/teacher.py — Academic Service

Mirrors: TeacherResponse, TeacherListResponse, CreateTeacherRequest,
UpdateTeacherRequest, AssignTeacherRequest.
"""
from rest_framework import serializers

from .common import EnumValueField, PageMetaSerializer


class TeacherResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    fullName = serializers.CharField(source="full_name")
    email = serializers.EmailField()
    status = EnumValueField()
    assignedCohortIds = serializers.ListField(
        child=serializers.UUIDField(), source="assigned_cohort_ids"
    )
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")


class TeacherListResponseSerializer(serializers.Serializer):
    teachers = TeacherResponseSerializer(many=True)
    pagination = PageMetaSerializer(required=False)


class CreateTeacherSerializer(serializers.Serializer):
    userId = serializers.UUIDField(source="user_id")
    fullName = serializers.CharField(source="full_name")
    email = serializers.EmailField()

class UpdateTeacherSerializer(serializers.Serializer):
    fullName = serializers.CharField(source="full_name", required=False)
    email = serializers.EmailField(required=False)


class AssignTeacherSerializer(serializers.Serializer):
    teacherId = serializers.UUIDField(source="teacher_id")