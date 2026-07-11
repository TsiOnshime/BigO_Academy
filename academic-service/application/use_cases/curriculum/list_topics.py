from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import Topic
from domain.enums import YearPhase
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class ListTopicsCommand:
    cohort_id: UUID
    year_phase: Optional[YearPhase] = None


class ListTopicsUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: ListTopicsCommand) -> list[Topic]:
        return self.curriculum_repository.find_topics_by_cohort(
            cohort_id=command.cohort_id,
            year_phase=command.year_phase,
        )