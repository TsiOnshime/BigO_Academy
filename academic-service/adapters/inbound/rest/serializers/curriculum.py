"""
adapters/inbound/rest/serializers/curriculum.py — Academic Service

Mirrors: TopicResponse, TopicListResponse, CreateTopicRequest,
UpdateTopicRequest, ReorderTopicsRequest, ProblemResponse,
ProblemListResponse, CreateProblemRequest, UpdateProblemRequest.
"""
from rest_framework import serializers

from domain.enums import ProblemDifficulty, ProblemSource

from .common import EnumValueField


class TopicResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField(allow_null=True, required=False)
    yearPhase = EnumValueField(source="year_phase")
    displayOrder = serializers.IntegerField(source="display_order")
    problemCount = serializers.IntegerField(source="problem_count")
    createdAt = serializers.DateTimeField(source="created_at")


class TopicListResponseSerializer(serializers.Serializer):
    topics = TopicResponseSerializer(many=True)


class CreateTopicSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    yearPhase = serializers.ChoiceField(choices=[1, 2], source="year_phase")
    displayOrder = serializers.IntegerField(source="display_order", required=False)


class UpdateTopicSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    displayOrder = serializers.IntegerField(source="display_order", required=False)


class ReorderTopicsSerializer(serializers.Serializer):
    orderedTopicIds = serializers.ListField(
        child=serializers.UUIDField(), source="ordered_topic_ids"
    )


class ProblemResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    topicId = serializers.UUIDField(source="topic_id")
    title = serializers.CharField()
    source = EnumValueField()
    externalUrl = serializers.URLField(source="external_url")
    difficulty = EnumValueField()
    createdAt = serializers.DateTimeField(source="created_at")


class ProblemListResponseSerializer(serializers.Serializer):
    problems = ProblemResponseSerializer(many=True)


class CreateProblemSerializer(serializers.Serializer):
    title = serializers.CharField()
    source = serializers.ChoiceField(choices=[s.value for s in ProblemSource])
    externalUrl = serializers.URLField(source="external_url")
    difficulty = serializers.ChoiceField(choices=[d.value for d in ProblemDifficulty])


class UpdateProblemSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    externalUrl = serializers.URLField(source="external_url", required=False)
    difficulty = serializers.ChoiceField(
        choices=[d.value for d in ProblemDifficulty], required=False
    )