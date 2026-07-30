from uuid import UUID, uuid4
from datetime import date
from typing import Optional

from domain.models import HistoricalMetric
from domain.enums import MetricType
from application.ports.outbound.historical_metrics_repository import (
    HistoricalMetricsRepositoryPort,
)
from core.models import HistoricalMetricModel


class DjangoHistoricalMetricsRepository(HistoricalMetricsRepositoryPort):

    def _to_domain(self, orm: HistoricalMetricModel) -> HistoricalMetric:
        return HistoricalMetric(
            id=orm.id,
            student_id=orm.student_id,
            snapshot_date=orm.snapshot_date,
            rank=orm.rank,
            rating=orm.rating,
            performance_score=orm.performance_score,
            consistency_score=orm.consistency_score,
            attendance_percentage=orm.attendance_percentage,
            problem_solved_count=orm.problem_solved_count,
        )

    def save(self, metric: HistoricalMetric) -> HistoricalMetric:
        orm, _ = HistoricalMetricModel.objects.update_or_create(
            student_id=metric.student_id,
            snapshot_date=metric.snapshot_date,
            defaults={
                "rank": metric.rank,
                "rating": metric.rating,
                "performance_score": metric.performance_score,
                "consistency_score": metric.consistency_score,
                "attendance_percentage": metric.attendance_percentage,
                "problem_solved_count": metric.problem_solved_count,
            },
        )
        return self._to_domain(orm)

    def find_by_student(
        self,
        student_id: UUID,
        metric_type: Optional[MetricType] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[HistoricalMetric]:
        queryset = HistoricalMetricModel.objects.filter(
            student_id=student_id
        )

        if from_date:
            queryset = queryset.filter(snapshot_date__gte=from_date)

        if to_date:
            queryset = queryset.filter(snapshot_date__lte=to_date)

        queryset = queryset.order_by("snapshot_date")

        return [self._to_domain(orm) for orm in queryset]

    def exists_for_date(
        self,
        student_id: UUID,
        snapshot_date: date,
    ) -> bool:
        return HistoricalMetricModel.objects.filter(
            student_id=student_id,
            snapshot_date=snapshot_date,
        ).exists()