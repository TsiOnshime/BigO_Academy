from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.models import Warning


class WarningRepositoryPort(ABC):

    @abstractmethod
    def save(self, warning: Warning) -> Warning:
        """create or update a warning"""

    @abstractmethod
    def find_by_id(self, warning_id: UUID) -> Optional[Warning]:
        """find a warning by id"""

    @abstractmethod
    def find_by_student(self, student_id: UUID) -> list[Warning]:
        """full warning history for a student"""

    @abstractmethod
    def count_active_warnings(self, student_id: UUID) -> int:
        """how many active (non-dismissed) warnings a student currently has"""

    @abstractmethod
    def find_escalated(self, cohort_id: UUID) -> list[Warning]:
        """admin view: students in a cohort with escalated (3rd) warnings"""