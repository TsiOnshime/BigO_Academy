from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.exceptions import StudentAnalyticsNotFoundError


@dataclass
class ProcessStudentPromotedCommand:
    student_id: UUID
    timestamp: Optional[str] = None


class ProcessStudentPromotedUseCase:
    """
    Kafka consumer target for: academic.student.promoted

    NOTE: the guide describes this as updating "year_level in
    analytics," but year_level isn't part of the StudentAnalytics
    domain model or the StudentAnalyticsRepositoryPort contract (it
    only exists as an unused column on StudentAnalyticsModel). Without
    extending the domain model/port, the meaningful thing this use
    case can do today is treat a promotion as the start of a fresh
    streak for the new year, while preserving longest_streak as a
    lifetime record. Add year_level to the domain model and port if
    you need it tracked and exposed via the API.
    """

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(self, command: ProcessStudentPromotedCommand) -> None:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            raise StudentAnalyticsNotFoundError(str(command.student_id))

        analytics.current_streak = 0

        self._student_analytics_repository.save(analytics)