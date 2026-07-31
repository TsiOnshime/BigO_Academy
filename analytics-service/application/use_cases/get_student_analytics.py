from dataclasses import dataclass
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.exceptions import StudentAnalyticsNotFoundError
from domain.models import StudentAnalytics


@dataclass
class GetStudentAnalyticsCommand:
    student_id: UUID


class GetStudentAnalyticsUseCase:
    """GET /analytics/students/{studentId}"""

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(self, command: GetStudentAnalyticsCommand) -> StudentAnalytics:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            raise StudentAnalyticsNotFoundError(str(command.student_id))
        return analytics