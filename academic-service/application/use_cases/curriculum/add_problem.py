from dataclasses import dataclass
from uuid import uuid4, UUID

from domain.models import Problem
from domain.enums import ProblemSource, ProblemDifficulty
from domain.exceptions import TopicNotFoundError
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class AddProblemCommand:
    topic_id: UUID
    title: str
    source: ProblemSource
    external_url: str
    difficulty: ProblemDifficulty


class AddProblemUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: AddProblemCommand) -> Problem:

        topic = self.curriculum_repository.find_topic_by_id(command.topic_id)
        if topic is None:
            raise TopicNotFoundError(str(command.topic_id))

        new_problem = Problem(
            id=uuid4(),
            topic_id=command.topic_id,
            title=command.title,
            source=command.source,
            external_url=command.external_url,
            difficulty=command.difficulty,
        )

        return self.curriculum_repository.save_problem(new_problem)