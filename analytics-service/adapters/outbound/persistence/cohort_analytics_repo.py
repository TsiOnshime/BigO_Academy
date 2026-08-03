from uuid import UUID
from typing import Optional

from domain.models import (
    CohortAnalytics,
    WarningStats,
    ProgressionStats,
)
from application.ports.outbound.cohort_analytics_repository import (
    CohortAnalyticsRepositoryPort,
)
from core.models import CohortAnalyticsModel


class DjangoCohortAnalyticsRepository(CohortAnalyticsRepositoryPort):

    def _to_domain(self, orm: CohortAnalyticsModel) -> CohortAnalytics:
        return CohortAnalytics(
            cohort_id=orm.cohort_id,
            cohort_name=orm.cohort_name,
            total_students=orm.total_students,
            average_performance_score=orm.average_performance_score,
            average_attendance_percentage=orm.average_attendance_percentage,
            average_consistency_score=orm.average_consistency_score,
            warning_stats=WarningStats(
                total_issued=orm.total_warnings_issued,
                total_resolved=orm.total_warnings_resolved,
                active_warnings=orm.active_warnings,
                students_on_probation=orm.students_on_probation,
            ),
            progression_stats=ProgressionStats(
                promoted_to_year2=orm.promoted_to_year2,
                graduated=orm.graduated,
                dropped=orm.dropped,
                active=orm.active_students,
            ),
            last_updated=orm.last_updated.isoformat(),
        )

    def save(self, analytics: CohortAnalytics) -> CohortAnalytics:
        orm, _ = CohortAnalyticsModel.objects.update_or_create(
            cohort_id=analytics.cohort_id,
            defaults={
                "cohort_name": analytics.cohort_name,
                "total_students": analytics.total_students,
                "average_performance_score": analytics.average_performance_score,
                "average_attendance_percentage": analytics.average_attendance_percentage,
                "average_consistency_score": analytics.average_consistency_score,
                "total_warnings_issued": analytics.warning_stats.total_issued,
                "total_warnings_resolved": analytics.warning_stats.total_resolved,
                "active_warnings": analytics.warning_stats.active_warnings,
                "students_on_probation": analytics.warning_stats.students_on_probation,
                "promoted_to_year2": analytics.progression_stats.promoted_to_year2,
                "graduated": analytics.progression_stats.graduated,
                "dropped": analytics.progression_stats.dropped,
                "active_students": analytics.progression_stats.active,
            },
        )
        return self._to_domain(orm)

    def find_by_cohort_id(
        self,
        cohort_id: UUID,
    ) -> Optional[CohortAnalytics]:
        try:
            return self._to_domain(
                CohortAnalyticsModel.objects.get(cohort_id=cohort_id)
            )
        except CohortAnalyticsModel.DoesNotExist:
            return None

    def find_all(self) -> list[CohortAnalytics]:
        return [
            self._to_domain(orm)
            for orm in CohortAnalyticsModel.objects.all()
        ]