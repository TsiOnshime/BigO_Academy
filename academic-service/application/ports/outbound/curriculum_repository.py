from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional

from domain.models import Topic, Problem
from domain.enums import YearPhase


class CurriculumRepositoryPort(ABC):

    # ── Topics ──────────────────────────────────────────────────────────

    @abstractmethod
    def save_topic(self, topic: Topic) -> Topic:
        """create or update a topic"""

    @abstractmethod
    def find_topic_by_id(self, topic_id: UUID) -> Optional[Topic]:
        """find a topic by id"""

    @abstractmethod
    def find_topics_by_cohort(self, cohort_id: UUID, year_phase: Optional[YearPhase] = None) -> list[Topic]:
        """list topics for a cohort's curriculum, optionally filtered by year phase. Ordered by display_order ascending."""

    @abstractmethod
    def delete_topic(self, topic_id: UUID) -> None:
        """delete a topic. Problems cascade delete automatically."""

    @abstractmethod
    def reorder_topics(self, ordered_topic_ids: list[UUID]) -> None:
        """bulk update display_order to match the given order"""

    # ── Problems ────────────────────────────────────────────────────────

    @abstractmethod
    def save_problem(self, problem: Problem) -> Problem:
        """create or update a problem"""

    @abstractmethod
    def find_problem_by_id(self, problem_id: UUID) -> Optional[Problem]:
        """find a problem by id"""

    @abstractmethod
    def find_problems_by_topic(self, topic_id: UUID) -> list[Problem]:
        """list all problems belonging to a topic"""

    @abstractmethod
    def delete_problem(self, problem_id: UUID) -> None:
        """delete a problem"""