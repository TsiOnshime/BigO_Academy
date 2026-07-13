from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.models import ProblemProgress


class ProgressRepositoryPort(ABC):

    @abstractmethod
    def save(self, progress: ProblemProgress) -> ProblemProgress:
        """create or update a student's progress record on a problem. Use get_or_create internally — one record per student per problem."""

    @abstractmethod
    def find_by_student_and_problem(self, student_id: UUID, problem_id: UUID) -> Optional[ProblemProgress]:
        """find a single student's progress on a single problem"""

    @abstractmethod
    def find_all_by_student(self, student_id: UUID, topic_id: Optional[UUID] = None) -> list[ProblemProgress]:
        """full progress sheet for a student, optionally filtered by topic"""

    @abstractmethod
    def count_solved_by_student(self, student_id: UUID) -> int:
        """
        COUNT query — total number of problems solved by this student.
        More efficient than fetching all records and counting in Python.
        total number of problems solved by a student
        """