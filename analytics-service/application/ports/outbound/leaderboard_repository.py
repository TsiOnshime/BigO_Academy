from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from domain.models import LeaderboardEntry

class LeaderboardRepositoryPort(ABC):
    @abstractmethod
    def save_entry(self, entry: LeaderboardEntry) -> LeaderboardEntry:
        """Insert or update a single leaderboard entry."""
        ...

    @abstractmethod
    def save_all(self, entries: list[LeaderboardEntry]) -> None:
        """Bulk upsert leaderboard entries. Used by refresh job."""
        ...

    @abstractmethod
    def find_global(
        self, page: int = 0, size: int = 20
    ) -> list[LeaderboardEntry]:
        """Return global leaderboard ordered by rank ascending."""
        ...

    @abstractmethod
    def find_by_cohort(
        self, cohort_id: UUID, page: int = 0, size: int = 20
    ) -> list[LeaderboardEntry]:
        """Return cohort leaderboard ordered by rank ascending."""
        ...

    @abstractmethod
    def get_last_refreshed(self) -> str:
        """Return ISO timestamp of last leaderboard refresh."""
        ...