from dataclasses import dataclass
from datetime import date
from uuid import UUID
from typing import Optional

from domain.models import Cohort
from domain.exceptions import CohortNotFoundError, CohortArchivedError
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class UpdateCohortCommand:
    cohort_id: UUID
    name: Optional[str] = None
    student_capacity: Optional[int] = None
    expected_graduation_date: Optional[date] = None


class UpdateCohortUseCase:

    def __init__(
        self,
        cohort_repository: CohortRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.cohort_repository = cohort_repository
        self.event_publisher = event_publisher

    def execute(self, command: UpdateCohortCommand) -> Cohort:

        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))

        # Cannot update an archived cohort
        if not cohort.is_active():
            raise CohortArchivedError(str(command.cohort_id))

        if command.name is not None:
            cohort.name = command.name
        if command.student_capacity is not None:
            cohort.student_capacity = command.student_capacity
        if command.expected_graduation_date is not None:
            cohort.expected_graduation_date = command.expected_graduation_date

        saved_cohort = self.cohort_repository.save(cohort)
        self.event_publisher.publish_cohort_updated(saved_cohort)

        return saved_cohort