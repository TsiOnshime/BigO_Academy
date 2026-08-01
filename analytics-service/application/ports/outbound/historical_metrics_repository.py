from abc import ABC, abstractmethod
from uuid import UUID
from datetime import date
from typing import Optional
from domain.models import HistoricalMetric
from domain.enums import MetricType

class HistoricalMetricsRepositoryPort(ABC):
    @abstractmethod
    def save(self, metric: HistoricalMetric) -> HistoricalMetric:
        """Save a single historical metric snapshot."""
        ...

    @abstractmethod
    def find_by_student(
        self,
        student_id: UUID,
        metric_type: Optional[MetricType] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[HistoricalMetric]:
        """
        Return historical snapshots for a student.
        Optionally filter by metric_type and date range.
        Ordered by snapshot_date ascending.
        """
        ...

    @abstractmethod
    def exists_for_date(
        self, student_id: UUID, snapshot_date: date
    ) -> bool:
        """
        Return True if a snapshot already exists for this
        student and date. Prevents duplicate daily snapshots.
        """
        ...