"""
adapters/inbound/rest/serializers/progress.py — Academic Service

Mirrors: ProgressSheetResponse, TopicProgressSummary,
ProblemProgressResponse, UpdateProgressRequest.

Spec mismatch worth flagging: the OpenAPI spec nests progress by topic
(ProgressSheetResponse.topicProgress[].problems[]), but
GetStudentProgressUseCase (get_student_progress.py) returns a *flat*
list[ProblemProgress] with no topic grouping. Grouping the flat list by
topic (and looking up topic titles) is a views.py concern — the view
would need to call curriculum_repository itself to build the grouped
shape. ProgressSheetResponseSerializer below matches what the use case
actually returns (flat); TopicProgressSummarySerializer is provided for
a view that chooses to do that extra grouping work.
"""
from rest_framework import serializers


class ProblemProgressResponseSerializer(serializers.Serializer):
    problemId = serializers.UUIDField(source="problem_id")
    # view-supplied: not on domain.ProblemProgress — the view looks up the
    # problem (via curriculum_repository) and adds `problem_title`.
    problemTitle = serializers.CharField(source="problem_title", required=False)
    solved = serializers.BooleanField()
    attemptCount = serializers.IntegerField(source="attempt_count")
    solveTimeMinutes = serializers.IntegerField(source="solve_time_minutes")
    verifiedByTeacher = serializers.BooleanField(source="verified_by_teacher")
    solvedAt = serializers.DateTimeField(source="solved_at", allow_null=True)


class TopicProgressSummarySerializer(serializers.Serializer):
    """For a view that groups the flat use-case result by topic —
    see module docstring."""

    topicId = serializers.UUIDField(source="topic_id")
    topicTitle = serializers.CharField(source="topic_title")
    totalProblems = serializers.IntegerField(source="total_problems")
    solvedCount = serializers.IntegerField(source="solved_count")
    problems = ProblemProgressResponseSerializer(many=True)


class ProgressSheetResponseSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    totalProblems = serializers.IntegerField(source="total_problems")
    solvedCount = serializers.IntegerField(source="solved_count")
    completionPercentage = serializers.FloatField(source="completion_percentage")
    # Flat, matching GetStudentProgressResult.progress — see module
    # docstring for the spec's nested topicProgress shape instead.
    progress = ProblemProgressResponseSerializer(many=True)


class UpdateProgressSerializer(serializers.Serializer):
    solved = serializers.BooleanField()
    attemptCount = serializers.IntegerField(
        source="attempt_count", required=False, min_value=1
    )
    solveTimeMinutes = serializers.IntegerField(
        source="solve_time_minutes", required=False, min_value=0
    )
    verifiedByTeacher = serializers.BooleanField(
        source="verified_by_teacher", required=False
    )