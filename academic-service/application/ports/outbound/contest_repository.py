from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.models import Contest, ContestResult
from domain.enums import ContestStatus


class ContestRepositoryPort(ABC):

    @abstractmethod
    def save(self, contest: Contest) -> Contest:
        """create or update a contest"""

    @abstractmethod
    def find_by_id(self, contest_id: UUID) -> Optional[Contest]:
        """find a contest by id"""

    @abstractmethod
    def find_all_by_cohort(self, cohort_id: UUID, status: Optional[ContestStatus] = None) -> list[Contest]:
        """list contests for a cohort, optionally filtered by status"""

    @abstractmethod
    def save_results(self, contest_id: UUID, results: list[ContestResult]) -> None:
        """Bulk insert ContestResult records for a finished contest.
        Updates contest status to FINISHED."""

    @abstractmethod
    def find_results_by_contest(self, contest_id: UUID) -> list[ContestResult]:
        """list results submitted for a contest"""
    @abstractmethod
    def has_results(self, contest_id: UUID) -> bool:
        """
        Return True if results already submitted.
        Prevents double submission — checked before save_results.
        """