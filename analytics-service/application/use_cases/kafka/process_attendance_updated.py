from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.models import ContestStats, StudentAnalytics

ATTENDANCE_EMA_ALPHA = 0.1
STATUS_SCORES = {
    "PRESENT": 100.0,
    "LATE": 50.0,
    "EXCUSED": 100.0,
    "ABSENT": 0.0,
}
PERFORMANCE_ATTENDANCE_WEIGHT = 0.4
PERFORMANCE_CONSISTENCY_WEIGHT = 0.4
PERFORMANCE_VOLUME_WEIGHT = 0.2
PERFORMANCE_VOLUME_CAP = 100


@dataclass
class ProcessAttendanceUpdatedCommand:
    student_id: UUID
    session_id: UUID
    status: str
    timestamp: Optional[str] = None


class ProcessAttendanceUpdatedUseCase:
    """
    Kafka consumer target for: academic.attendance.updated

    attendance_percentage is modeled as an exponential moving average
    over per-session attendance rather than a running count, since
    this service never receives the student's full session history
    (only one status update at a time).
    """

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(self, command: ProcessAttendanceUpdatedCommand) -> None:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            analytics = self._new_student_analytics(command.student_id)

        session_score = STATUS_SCORES.get(command.status.upper(), 0.0)
        analytics.attendance_percentage = round(
            analytics.attendance_percentage * (1 - ATTENDANCE_EMA_ALPHA)
            + session_score * ATTENDANCE_EMA_ALPHA,
            2,
        )
        analytics.performance_score = self._recompute_performance_score(
            analytics
        )

        self._student_analytics_repository.save(analytics)

    @staticmethod
    def _recompute_performance_score(analytics: StudentAnalytics) -> float:
        volume_component = min(
            analytics.problem_solved_count, PERFORMANCE_VOLUME_CAP
        )
        score = (
            analytics.attendance_percentage * PERFORMANCE_ATTENDANCE_WEIGHT
            + analytics.consistency_score * PERFORMANCE_CONSISTENCY_WEIGHT
            + volume_component * PERFORMANCE_VOLUME_WEIGHT
        )
        return round(score, 2)

    @staticmethod
    def _new_student_analytics(student_id: UUID) -> StudentAnalytics:
        return StudentAnalytics(
            student_id=student_id,
            cohort_id=None,
            rank=0,
            rating=0.0,
            performance_score=0.0,
            consistency_score=0.0,
            attendance_percentage=0.0,
            problem_solved_count=0,
            current_streak=0,
            longest_streak=0,
            active_warning_count=0,
            contest_stats=ContestStats(
                total_contests_participated=0,
                average_rank=0.0,
                best_rank=0,
                total_problems_solved_in_contests=0,
            ),
        )