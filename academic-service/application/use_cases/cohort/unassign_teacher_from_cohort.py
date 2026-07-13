from dataclasses import dataclass
from uuid import UUID

from domain.exceptions import (
    CohortNotFoundError,
    TeacherNotFoundError,
)
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.teacher_repository import TeacherRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class UnassignTeacherFromCohortCommand:
    cohort_id: UUID
    teacher_id: UUID


class UnassignTeacherFromCohortUseCase:

    def __init__(
        self,
        cohort_repository: CohortRepositoryPort,
        teacher_repository: TeacherRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.cohort_repository = cohort_repository
        self.teacher_repository = teacher_repository
        self.event_publisher = event_publisher

    def execute(self, command: UnassignTeacherFromCohortCommand) -> None:

        # Both must exist
        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))

        teacher = self.teacher_repository.find_by_id(command.teacher_id)
        if teacher is None:
            raise TeacherNotFoundError(str(command.teacher_id))

        self.cohort_repository.unassign_teacher(
            command.cohort_id,
            command.teacher_id,
        )

        self.event_publisher.publish_teacher_unassigned_from_cohort(
            command.teacher_id,
            command.cohort_id,
        )