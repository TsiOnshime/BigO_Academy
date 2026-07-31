from dataclasses import dataclass
from uuid import UUID

from application.ports.outbound.cohort_analytics_repository import (
    CohortAnalyticsRepositoryPort,
)
from domain.exceptions import CohortAnalyticsNotFoundError
from domain.models import CohortAnalytics


@dataclass
class GetCohortAnalyticsCommand:
    cohort_id: UUID


class GetCohortAnalyticsUseCase:
    """GET /analytics/admin/cohorts/{cohortId}"""

    def __init__(
        self, cohort_analytics_repository: CohortAnalyticsRepositoryPort
    ):
        self._cohort_analytics_repository = cohort_analytics_repository

    def execute(self, command: GetCohortAnalyticsCommand) -> CohortAnalytics:
        analytics = self._cohort_analytics_repository.find_by_cohort_id(
            command.cohort_id
        )
        if analytics is None:
            raise CohortAnalyticsNotFoundError(str(command.cohort_id))
        return analytics