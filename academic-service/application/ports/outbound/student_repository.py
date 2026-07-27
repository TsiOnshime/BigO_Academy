from abc import ABC, abstractmethod
from uuid import UUID
from domain.models import Student
from domain.enums import StudentStatus
from typing import Optional
class StudentRepositoryPort(ABC):
    
    @abstractmethod
    def save(self, student: Student) -> Student:
        """create a new student profile, or update existing one"""
    
    @abstractmethod
    def find_by_id(self, student_id: UUID) -> Optional[Student]:
        """Find a student by academic service id. returns none if not found"""
    
    @abstractmethod
    def find_by_user_id(self, user_id: UUID) -> Optional[Student]:
        """find a student by their auth service user id"""
        
    @abstractmethod
    def find_all(self, cohort_id: Optional[UUID] = None, status: Optional[StudentStatus] = None) -> list[Student]:
        """list all students, optionally filtered by cohort or status"""
        
    @abstractmethod
    def exists_by_user_id(self, user_id) -> bool:
        """checks if a student profile already exists"""