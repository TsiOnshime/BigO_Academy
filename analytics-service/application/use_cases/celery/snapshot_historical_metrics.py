from datetime import datetime, timezone
from uuid import uuid4

from application.ports.outbound.historical_metrics_repository import (
    HistoricalMetricsRepositoryPort,
)
from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.models import HistoricalMetric


class SnapshotHistoricalMetricsUseCase:
    """
    Runs daily at midnight via Celery (infrastructure/jobs/celery_app.py).

    Takes one HistoricalMetric snapshot per student per day, for trend
    charts (GET /analytics/students/{studentId}/history). Skips
    students who already have a snapshot for today so the job is safe
    to re-run (e.g. if Celery Beat fires twice, or the job is
    triggered manually) -- HistoricalMetricModel also has a unique
    constraint on (student_id, snapshot_date) as a second line of
    defense.
    """

    def __init__(
        self,
        student_analytics_repository: StudentAnalyticsRepositoryPort,
        historical_metrics_repository: HistoricalMetricsRepositoryPort,
    ):
        self._student_analytics_repository = student_analytics_repository
        self._historical_metrics_repository = historical_metrics_repository

    def execute(self) -> None:
        today = datetime.now(timezone.utc).date()

        for student in self._student_analytics_repository.find_all():
            if self._historical_metrics_repository.exists_for_date(
                student.student_id, today
            ):
                continue

            self._historical_metrics_repository.save(
                HistoricalMetric(
                    id=uuid4(),
                    student_id=student.student_id,
                    snapshot_date=today,
                    rank=student.rank,
                    rating=student.rating,
                    performance_score=student.performance_score,
                    consistency_score=student.consistency_score,
                    attendance_percentage=student.attendance_percentage,
                    problem_solved_count=student.problem_solved_count,
                )
            )