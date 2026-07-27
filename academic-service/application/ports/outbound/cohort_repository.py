from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.models import Cohort
from domain.enums import CohortStatus
class CohortRepositoryPort(ABC):
    
    @abstractmethod
    def save(self, cohort: Cohort) -> Cohort:
        """saves or updates a cohort"""
    
    @abstractmethod
    def find_by_id(self, cohort_id: UUID) -> Optional[Cohort]:
        """find a cohort by id"""
        
    @abstractmethod
    def find_all(self, status: Optional[CohortStatus] = None) -> list[Cohort]:
        """find all cohort with status being optional filter"""
        
    @abstractmethod
    def assign_student(self, cohort_id: UUID, student_id: UUID) -> None:
        """assign a student to a cohort. updates enrolled_student_count automatically"""
    
    @abstractmethod
    def unassign_student(self, cohort_id: UUID, student_id: UUID) -> None:
        """remove a student from a cohort. updates enrolled_student_count"""

    @abstractmethod
    def assign_teacher(self, cohort_id: UUID, teacher_id: UUID) -> None:
        """Add teacher to cohort via ManyToMany. Updates teacher_count."""

    @abstractmethod
    def unassign_teacher(self, cohort_id: UUID, teacher_id: UUID) -> None:
        """remove a teacher from a cohort. Updates teacher_count."""

    @abstractmethod
    def student_in_cohort(self, cohort_id: UUID, student_id: UUID) -> bool:
        """check if a student is in cohort"""
    @abstractmethod
    def teacher_in_cohort(self, cohort_id: UUID, teacher_id: UUID) -> bool:
        """checks if a teacher is in cohort"""