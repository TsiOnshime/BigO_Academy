from dataclasses import dataclass
from uuid import UUID

from domain.models import Cohort
from domain.enums import CohortStatus
from domain.exceptions import CohortNotFoundError
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class ArchiveCohortCommand:
    cohort_id: UUID


class ArchiveCohortUseCase:

    def __init__(
        self,
        cohort_repository: CohortRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.cohort_repository = cohort_repository
        self.event_publisher = event_publisher

    def execute(self, command: ArchiveCohortCommand) -> Cohort:

        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))

        # Idempotent — archiving an already archived cohort is harmless
        cohort.status = CohortStatus.ARCHIVED
        saved_cohort = self.cohort_repository.save(cohort)

        self.event_publisher.publish_cohort_archived(saved_cohort)

        return saved_cohort