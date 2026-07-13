from dataclasses import dataclass
from uuid import UUID

from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class ReorderTopicsCommand:
    ordered_topic_ids: list[UUID]


class ReorderTopicsUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: ReorderTopicsCommand) -> None:
        """
        The list position determines the new display_order.
        First item gets order=0, second gets order=1, etc.
        """
        self.curriculum_repository.reorder_topics(command.ordered_topic_ids)