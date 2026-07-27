from dataclasses import dataclass
from uuid import UUID

from domain.exceptions import TopicNotFoundError
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class DeleteTopicCommand:
    topic_id: UUID


class DeleteTopicUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: DeleteTopicCommand) -> None:

        topic = self.curriculum_repository.find_topic_by_id(command.topic_id)
        if topic is None:
            raise TopicNotFoundError(str(command.topic_id))

        # Cascade delete
        self.curriculum_repository.delete_topic(command.topic_id)