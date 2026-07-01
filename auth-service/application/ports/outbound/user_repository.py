from abc import ABC, abstractmethod

from uuid import UUID
from domain.models import User


class UserRepositoryPort(ABC):
    
    @abstractmethod
    def save(self, user: User) -> User:
        """Persist a new or updated user. Returns the saved user."""
        
    @abstractmethod
    def find_by_email(self, email:str) -> User | None:
        """Find a user by email. Returns None if not found"""
    @abstractmethod
    def find_by_id(self, user_id: UUID) -> User | None:
        """Find a user by their UUID. Returns None if not found"""
    @abstractmethod
    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered"""
        
        