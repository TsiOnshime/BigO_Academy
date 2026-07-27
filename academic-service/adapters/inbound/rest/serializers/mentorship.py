"""
adapters/inbound/rest/serializers/mentorship.py — Academic Service

Mirrors: MentorshipSessionResponse, MentorshipSessionListResponse,
CreateMentorshipSessionRequest, UpdateMentorshipSessionRequest.
"""
from rest_framework import serializers

from domain.enums import MentorshipSessionStatus

from .common import EnumValueField, PageMetaSerializer


class MentorshipSessionResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    teacherId = serializers.UUIDField(source="teacher_id")
    # view-supplied: not on domain.MentorshipSession — the view looks up
    # the teacher and adds `teacher_name`.
    teacherName = serializers.CharField(source="teacher_name", required=False)
    studentId = serializers.UUIDField(source="student_id")
    # view-supplied: same as teacherName, looked up from student_repository.
    studentName = serializers.CharField(source="student_name", required=False)
    scheduledAt = serializers.DateTimeField(source="scheduled_at")
    status = EnumValueField()
    notes = serializers.CharField(allow_null=True, required=False)
    createdAt = serializers.DateTimeField(source="created_at")


class MentorshipSessionListResponseSerializer(serializers.Serializer):
    sessions = MentorshipSessionResponseSerializer(many=True)
    pagination = PageMetaSerializer(required=False)


class CreateMentorshipSessionSerializer(serializers.Serializer):
    teacherId = serializers.UUIDField(source="teacher_id")
    studentId = serializers.UUIDField(source="student_id")
    scheduledAt = serializers.DateTimeField(source="scheduled_at")


class UpdateMentorshipSessionSerializer(serializers.Serializer):
    scheduledAt = serializers.DateTimeField(source="scheduled_at", required=False)
    status = serializers.ChoiceField(
        choices=[s.value for s in MentorshipSessionStatus], required=False
    )
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)