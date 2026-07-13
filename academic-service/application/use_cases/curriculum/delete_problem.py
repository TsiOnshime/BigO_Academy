from dataclasses import dataclass
from uuid import UUID

from domain.exceptions import ProblemNotFoundError
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class DeleteProblemCommand:
    problem_id: UUID


class DeleteProblemUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: DeleteProblemCommand) -> None:

        problem = self.curriculum_repository.find_problem_by_id(command.problem_id)
        if problem is None:
            raise ProblemNotFoundError(str(command.problem_id))

        self.curriculum_repository.delete_problem(command.problem_id)