from dataclasses import dataclass
from uuid import UUID

from domain.models import Topic
from domain.exceptions import TopicNotFoundError
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class GetTopicCommand:
    topic_id: UUID


class GetTopicUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: GetTopicCommand) -> Topic:

        topic = self.curriculum_repository.find_topic_by_id(command.topic_id)
        if topic is None:
            raise TopicNotFoundError(str(command.topic_id))

        return topic