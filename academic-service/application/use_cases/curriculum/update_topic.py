from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import Topic
from domain.exceptions import TopicNotFoundError
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class UpdateTopicCommand:
    topic_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


class UpdateTopicUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: UpdateTopicCommand) -> Topic:

        topic = self.curriculum_repository.find_topic_by_id(command.topic_id)
        if topic is None:
            raise TopicNotFoundError(str(command.topic_id))

        if command.title is not None:
            topic.title = command.title
        if command.description is not None:
            topic.description = command.description
        if command.display_order is not None:
            topic.display_order = command.display_order

        return self.curriculum_repository.save_topic(topic)