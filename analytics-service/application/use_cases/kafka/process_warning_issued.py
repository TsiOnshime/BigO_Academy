from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.models import ContestStats, StudentAnalytics


@dataclass
class ProcessWarningIssuedCommand:
    student_id: UUID
    warning_id: UUID
    warning_type: str
    timestamp: Optional[str] = None


class ProcessWarningIssuedUseCase:
    """Kafka consumer target for: academic.warning.issued"""

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(self, command: ProcessWarningIssuedCommand) -> None:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            analytics = self._new_student_analytics(command.student_id)

        analytics.active_warning_count += 1

        self._student_analytics_repository.save(analytics)

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