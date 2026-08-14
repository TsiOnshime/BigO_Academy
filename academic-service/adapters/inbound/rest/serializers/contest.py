"""
adapters/inbound/rest/serializers/contest.py — Academic Service

Mirrors: ContestResponse, ContestListResponse, CreateContestRequest,
ContestResultsResponse, ContestParticipantResult,
SubmitContestResultsRequest.

Note: ContestResponse.source is a fixed single-value enum ([CODEFORCES])
in the spec, but domain.Contest has no `source` field at all — contests
in this domain are always sourced from Codeforces, so it's rendered as a
constant rather than read off the domain object.
"""
from rest_framework import serializers

from .common import EnumValueField


class ContestResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    cohortId = serializers.UUIDField(source="cohort_id")
    source = serializers.SerializerMethodField()
    externalContestUrl = serializers.URLField(source="external_contest_url")
    status = EnumValueField()
    scheduledAt = serializers.DateTimeField(source="scheduled_at")
    endedAt = serializers.DateTimeField(source="ended_at", allow_null=True)
    problemCount = serializers.IntegerField(source="problem_count")

    def get_source(self, obj) -> str:
        return "CODEFORCES"


class ContestListResponseSerializer(serializers.Serializer):
    contests = ContestResponseSerializer(many=True)
    pagination = serializers.DictField(required=False)


class CreateContestSerializer(serializers.Serializer):
    title = serializers.CharField()
    cohortId = serializers.UUIDField(source="cohort_id", required=False)
    externalContestUrl = serializers.URLField(source="external_contest_url")
    scheduledAt = serializers.DateTimeField(source="scheduled_at")
    problemCount = serializers.IntegerField(source="problem_count", required=False)


class ContestParticipantResultSerializer(serializers.Serializer):
    """Shared shape for both SubmitContestResultsRequest.results (input)
    and ContestResultsResponse.results (output)."""

    studentId = serializers.UUIDField(source="student_id")
    studentName = serializers.CharField(source="student_name", required=False)
    contestRank = serializers.IntegerField(source="contest_rank")
    problemsSolved = serializers.IntegerField(source="problems_solved")
    participated = serializers.BooleanField()


class SubmitContestResultsSerializer(serializers.Serializer):
    results = ContestParticipantResultSerializer(many=True)


class ContestResultsResponseSerializer(serializers.Serializer):
    contestId = serializers.UUIDField(source="contest_id")
    # view-supplied: joined from contest_repository.find_by_id(...).title
    contestTitle = serializers.CharField(source="contest_title")
    results = ContestParticipantResultSerializer(many=True)