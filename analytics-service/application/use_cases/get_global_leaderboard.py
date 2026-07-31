from dataclasses import dataclass

from application.ports.outbound.leaderboard_repository import (
    LeaderboardRepositoryPort,
)
from domain.models import LeaderboardEntry


@dataclass
class GetGlobalLeaderboardCommand:
    page: int = 0
    size: int = 20


class GetGlobalLeaderboardUseCase:
    """GET /analytics/leaderboard"""

    def __init__(self, leaderboard_repository: LeaderboardRepositoryPort):
        self._leaderboard_repository = leaderboard_repository

    def execute(
        self, command: GetGlobalLeaderboardCommand
    ) -> list[LeaderboardEntry]:
        return self._leaderboard_repository.find_global(
            page=command.page, size=command.size
        )