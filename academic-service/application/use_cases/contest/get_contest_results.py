from dataclasses import dataclass
from uuid import UUID

from domain.models import ContestResult
from domain.exceptions import ContestNotFoundError
from application.ports.outbound.contest_repository import ContestRepositoryPort


@dataclass
class GetContestResultsCommand:
    contest_id: UUID


class GetContestResultsUseCase:

    def __init__(self, contest_repository: ContestRepositoryPort):
        self.contest_repository = contest_repository

    def execute(self, command: GetContestResultsCommand) -> list[ContestResult]:

        contest = self.contest_repository.find_by_id(command.contest_id)
        if contest is None:
            raise ContestNotFoundError(str(command.contest_id))

        return self.contest_repository.find_results_by_contest(command.contest_id)