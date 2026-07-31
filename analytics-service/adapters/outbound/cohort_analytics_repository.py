from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from domain.models import CohortAnalytics

class CohortAnalyticsRepositoryPort(ABC):
    @abstractmethod
    def save(self, analytics: CohortAnalytics) -> CohortAnalytics:
        """Insert or update cohort analytics."""
        ...

    @abstractmethod
    def find_by_cohort_id(
        self, cohort_id: UUID
    ) -> Optional[CohortAnalytics]:
        """Return cohort analytics. None if not found."""
        ...

    @abstractmethod
    def find_all(self) -> list[CohortAnalytics]:
        """Return analytics for all cohorts."""
        ...