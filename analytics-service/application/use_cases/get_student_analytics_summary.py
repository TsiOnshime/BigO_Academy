from dataclasses import dataclass
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.exceptions import StudentAnalyticsNotFoundError
from domain.models import StudentAnalytics


@dataclass
class GetStudentAnalyticsSummaryCommand:
    student_id: UUID


class GetStudentAnalyticsSummaryUseCase:
    """
    GET /analytics/students/{studentId}/summary

    Reuses the same StudentAnalytics model as the full view. The
    serializer (StudentAnalyticsSummarySerializer) is what actually
    trims the response down to the lighter summary shape, so this use
    case just needs to fetch the current record.
    """

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(
        self, command: GetStudentAnalyticsSummaryCommand
    ) -> StudentAnalytics:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            raise StudentAnalyticsNotFoundError(str(command.student_id))
        return analytics