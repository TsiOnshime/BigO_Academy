from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.exceptions import StudentAnalyticsNotFoundError


@dataclass
class ProcessWarningResolvedCommand:
    student_id: UUID
    warning_id: UUID
    timestamp: Optional[str] = None


class ProcessWarningResolvedUseCase:
    """
    Kafka consumer target for: academic.warning.resolved

    Unlike ProcessWarningIssuedUseCase, this does NOT create a fresh
    record when the student is unknown -- a warning can only be
    resolved if it was issued first, and issuing is what creates the
    analytics record. A missing record here means the events arrived
    out of order or something upstream is broken, so it's raised
    rather than silently swallowed.
    """

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(self, command: ProcessWarningResolvedCommand) -> None:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            raise StudentAnalyticsNotFoundError(str(command.student_id))

        analytics.active_warning_count = max(
            0, analytics.active_warning_count - 1
        )

        self._student_analytics_repository.save(analytics)