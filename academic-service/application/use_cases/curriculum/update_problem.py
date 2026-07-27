from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import Problem
from domain.enums import ProblemDifficulty
from domain.exceptions import ProblemNotFoundError
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort


@dataclass
class UpdateProblemCommand:
    problem_id: UUID
    title: Optional[str] = None
    external_url: Optional[str] = None
    difficulty: Optional[ProblemDifficulty] = None


class UpdateProblemUseCase:

    def __init__(self, curriculum_repository: CurriculumRepositoryPort):
        self.curriculum_repository = curriculum_repository

    def execute(self, command: UpdateProblemCommand) -> Problem:

        problem = self.curriculum_repository.find_problem_by_id(command.problem_id)
        if problem is None:
            raise ProblemNotFoundError(str(command.problem_id))

        if command.title is not None:
            problem.title = command.title
        if command.external_url is not None:
            problem.external_url = command.external_url
        if command.difficulty is not None:
            problem.difficulty = command.difficulty

        return self.curriculum_repository.save_problem(problem)