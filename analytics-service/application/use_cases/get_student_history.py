from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

from application.ports.outbound.historical_metrics_repository import (
    HistoricalMetricsRepositoryPort,
)
from domain.enums import MetricType
from domain.models import HistoricalMetric


@dataclass
class GetStudentHistoryCommand:
    student_id: UUID
    metric_type: Optional[MetricType] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class GetStudentHistoryUseCase:
    """GET /analytics/students/{studentId}/history"""

    def __init__(
        self,
        historical_metrics_repository: HistoricalMetricsRepositoryPort,
    ):
        self._historical_metrics_repository = historical_metrics_repository

    def execute(
        self, command: GetStudentHistoryCommand
    ) -> list[HistoricalMetric]:
        return self._historical_metrics_repository.find_by_student(
            student_id=command.student_id,
            metric_type=command.metric_type,
            from_date=command.from_date,
            to_date=command.to_date,
        )