from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.models import MentorshipSession


class MentorshipRepositoryPort(ABC):

    @abstractmethod
    def save(self, session: MentorshipSession) -> MentorshipSession:
        """create or update a mentorship session"""

    @abstractmethod
    def find_by_id(self, session_id: UUID) -> Optional[MentorshipSession]:
        """find a mentorship session by id"""

    @abstractmethod
    def find_by_student(self, student_id: UUID) -> list[MentorshipSession]:
        """list mentorship sessions for a student"""

    @abstractmethod
    def find_by_teacher(self, teacher_id: UUID) -> list[MentorshipSession]:
        """Return all sessions a teacher has scheduled."""