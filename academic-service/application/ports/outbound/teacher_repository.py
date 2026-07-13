from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.models import Teacher
from domain.enums import TeacherStatus

class TeacherRepositoryPort(ABC):
    
    @abstractmethod
    def save(self, teacher: Teacher) -> Teacher:
        """creates or updates a teacher profile"""
        
    @abstractmethod
    def find_by_id(self, teacher_id: UUID) -> Optional[Teacher]:
        """finds a teacher by their id"""
        
    @abstractmethod
    def find_by_user_id(self, user_id: UUID) -> Optional[Teacher]:
        """finds a teacher by their id from auth"""
    
    @abstractmethod
    def find_all(self, status: Optional[TeacherStatus] = None) -> list[Teacher]:
        """list with optional status filter"""
    
    @abstractmethod
    def exists_by_user_id(self, user_id: UUID):
        """checks if a teacher already exists"""