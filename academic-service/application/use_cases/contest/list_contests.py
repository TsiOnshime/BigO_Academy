from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import Contest
from domain.enums import ContestStatus
from application.ports.outbound.contest_repository import ContestRepositoryPort


@dataclass
class ListContestsCommand:
    cohort_id: UUID
    status: Optional[ContestStatus] = None


class ListContestsUseCase:

    def __init__(self, contest_repository: ContestRepositoryPort):
        self.contest_repository = contest_repository

    def execute(self, command: ListContestsCommand) -> list[Contest]:
        return self.contest_repository.find_all_by_cohort(
            cohort_id=command.cohort_id,
            status=command.status,
        )