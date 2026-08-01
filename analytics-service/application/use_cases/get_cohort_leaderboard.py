from dataclasses import dataclass
from uuid import UUID

from application.ports.outbound.leaderboard_repository import (
    LeaderboardRepositoryPort,
)
from domain.models import LeaderboardEntry


@dataclass
class GetCohortLeaderboardCommand:
    cohort_id: UUID
    page: int = 0
    size: int = 20


class GetCohortLeaderboardUseCase:
    """GET /analytics/leaderboard/cohorts/{cohortId}"""

    def __init__(self, leaderboard_repository: LeaderboardRepositoryPort):
        self._leaderboard_repository = leaderboard_repository

    def execute(
        self, command: GetCohortLeaderboardCommand
    ) -> list[LeaderboardEntry]:
        return self._leaderboard_repository.find_by_cohort(
            cohort_id=command.cohort_id,
            page=command.page,
            size=command.size,
        )