from dataclasses import dataclass
from uuid import UUID

from domain.models import Contest
from domain.exceptions import ContestNotFoundError
from application.ports.outbound.contest_repository import ContestRepositoryPort


@dataclass
class GetContestCommand:
    contest_id: UUID


class GetContestUseCase:

    def __init__(self, contest_repository: ContestRepositoryPort):
        self.contest_repository = contest_repository

    def execute(self, command: GetContestCommand) -> Contest:

        contest = self.contest_repository.find_by_id(command.contest_id)
        if contest is None:
            raise ContestNotFoundError(str(command.contest_id))

        return contest