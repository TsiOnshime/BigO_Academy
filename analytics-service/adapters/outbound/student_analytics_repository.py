from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from domain.models import StudentAnalytics

class StudentAnalyticsRepositoryPort(ABC):
    @abstractmethod
    def save(self, analytics: StudentAnalytics) -> StudentAnalytics:
        """Insert or update student analytics record."""
        ...

    @abstractmethod
    def find_by_student_id(self, student_id: UUID) -> Optional[StudentAnalytics]:
        """Fetch student analytics by student_id. Returns None if not found."""
        ...

    @abstractmethod
    def find_all_by_cohort(self, cohort_id: UUID) -> list[StudentAnalytics]:
        """Return all student analytics records for a cohort."""
        ...

    @abstractmethod
    def find_top_performers(
        self, cohort_id: UUID, limit: int = 10
    ) -> list[StudentAnalytics]:
        """Return top N students by performance_score for a cohort."""
        ...

    @abstractmethod
    def find_at_risk(self, cohort_id: UUID) -> list[StudentAnalytics]:
        """
        Return students with:
        - attendance_percentage < 60.0 OR
        - performance_score < 40.0 OR
        - active_warning_count >= 1
        """
        ...