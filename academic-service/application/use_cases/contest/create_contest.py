from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4, UUID

from domain.models import Contest
from domain.enums import ContestStatus
from domain.exceptions import CohortNotFoundError
from application.ports.outbound.contest_repository import ContestRepositoryPort
from application.ports.outbound.cohort_repository import CohortRepositoryPort


@dataclass
class CreateContestCommand:
    title: str
    cohort_id: UUID
    external_contest_url: str
    scheduled_at: datetime
    problem_count: int = 0


class CreateContestUseCase:

    def __init__(
        self,
        contest_repository: ContestRepositoryPort,
        cohort_repository: CohortRepositoryPort,
    ):
        self.contest_repository = contest_repository
        self.cohort_repository = cohort_repository

    def execute(self, command: CreateContestCommand) -> Contest:

        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))

        new_contest = Contest(
            id=uuid4(),
            title=command.title,
            cohort_id=command.cohort_id,
            external_contest_url=command.external_contest_url,
            status=ContestStatus.UPCOMING,
            scheduled_at=command.scheduled_at,
            ended_at=None,
            problem_count=command.problem_count,
            results=[],
        )

        return self.contest_repository.save(new_contest)