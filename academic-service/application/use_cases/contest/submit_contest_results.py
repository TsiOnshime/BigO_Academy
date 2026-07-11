from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from domain.models import Contest, ContestResult
from domain.enums import ContestStatus
from domain.exceptions import (
    ContestNotFoundError,
    ContestResultsAlreadySubmittedError,
    ContestNotFinishedError,
)
from application.ports.outbound.contest_repository import ContestRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class ContestResultInput:
    student_id: UUID
    student_name: str
    contest_rank: int
    problems_solved: int
    participated: bool


@dataclass
class SubmitContestResultsCommand:
    contest_id: UUID
    results: list[ContestResultInput]


class SubmitContestResultsUseCase:

    def __init__(
        self,
        contest_repository: ContestRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.contest_repository = contest_repository
        self.event_publisher = event_publisher

    def execute(self, command: SubmitContestResultsCommand) -> Contest:

        contest = self.contest_repository.find_by_id(command.contest_id)
        if contest is None:
            raise ContestNotFoundError(str(command.contest_id))

        # Cannot submit results twice
        if self.contest_repository.has_results(command.contest_id):
            raise ContestResultsAlreadySubmittedError(str(command.contest_id))

        # Build result domain objects
        results = [
            ContestResult(
                student_id=r.student_id,
                student_name=r.student_name,
                contest_rank=r.contest_rank,
                problems_solved=r.problems_solved,
                participated=r.participated,
            )
            for r in command.results
        ]

        # Mark contest as finished
        contest.status = ContestStatus.FINISHED
        contest.ended_at = datetime.now(timezone.utc)
        contest.results = results

        # Save results and update contest status
        self.contest_repository.save_results(command.contest_id, results)
        saved_contest = self.contest_repository.save(contest)

        # Publish event — Analytics updates ratings and rankings
        self.event_publisher.publish_contest_finished(
            contest_id=command.contest_id,
            cohort_id=contest.cohort_id,
            results=results,
        )

        return saved_contest