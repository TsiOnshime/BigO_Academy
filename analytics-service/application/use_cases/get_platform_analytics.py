from datetime import datetime, timezone

from application.ports.outbound.cohort_analytics_repository import (
    CohortAnalyticsRepositoryPort,
)
from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.models import PlatformAnalytics


class GetPlatformAnalyticsUseCase:
    """
    GET /analytics/admin/platform

    No command object -- this is a platform-wide aggregate with no
    input parameters, per the guide.

    NOTE ON ASSUMPTIONS:
    - `total_teachers` can't be computed here: the Analytics Service
      has no repository or event stream carrying teacher headcount
      (that data lives in the Auth/Academic services). Defaulted to 0
      with a TODO; wire in a real source once available.
    - `CohortAnalyticsModel` has no explicit "archived" flag, so a
      cohort with zero currently-active students is treated as
      archived and everything else as active. Replace with a real
      status field if the Academic Service starts publishing it.
    """

    def __init__(
        self,
        student_analytics_repository: StudentAnalyticsRepositoryPort,
        cohort_analytics_repository: CohortAnalyticsRepositoryPort,
    ):
        self._student_analytics_repository = student_analytics_repository
        self._cohort_analytics_repository = cohort_analytics_repository

    def execute(self) -> PlatformAnalytics:
        cohorts = self._cohort_analytics_repository.find_all()

        total_students = sum(c.total_students for c in cohorts)
        active_cohorts = [c for c in cohorts if c.progression_stats.active > 0]
        archived_cohorts = [
            c for c in cohorts if c.progression_stats.active == 0
        ]

        overall_avg_performance = self._weighted_average(
            cohorts, lambda c: c.average_performance_score
        )
        overall_avg_attendance = self._weighted_average(
            cohorts, lambda c: c.average_attendance_percentage
        )

        total_warnings_issued = sum(
            c.warning_stats.total_issued for c in cohorts
        )
        students_on_probation = sum(
            c.warning_stats.students_on_probation for c in cohorts
        )
        students_dropped = sum(c.progression_stats.dropped for c in cohorts)
        total_graduates = sum(c.progression_stats.graduated for c in cohorts)

        return PlatformAnalytics(
            total_students=total_students,
            total_teachers=0,  # TODO: no teacher data source in this service
            total_active_cohorts=len(active_cohorts),
            total_archived_cohorts=len(archived_cohorts),
            overall_average_performance_score=overall_avg_performance,
            overall_average_attendance_percentage=overall_avg_attendance,
            total_warnings_issued=total_warnings_issued,
            students_on_probation=students_on_probation,
            students_dropped=students_dropped,
            total_graduates=total_graduates,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _weighted_average(cohorts, value_fn) -> float:
        total_weight = sum(c.total_students for c in cohorts)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(
            value_fn(c) * c.total_students for c in cohorts
        )
        return round(weighted_sum / total_weight, 2)