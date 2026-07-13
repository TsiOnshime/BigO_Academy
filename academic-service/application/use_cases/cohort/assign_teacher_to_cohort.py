from dataclasses import dataclass
from uuid import UUID

from domain.exceptions import (
    CohortNotFoundError,
    TeacherNotFoundError,
    TeacherAlreadyInCohortError,
    CohortArchivedError,
)
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.teacher_repository import TeacherRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class AssignTeacherToCohortCommand:
    cohort_id: UUID
    teacher_id: UUID


class AssignTeacherToCohortUseCase:

    def __init__(
        self,
        cohort_repository: CohortRepositoryPort,
        teacher_repository: TeacherRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.cohort_repository = cohort_repository
        self.teacher_repository = teacher_repository
        self.event_publisher = event_publisher

    def execute(self, command: AssignTeacherToCohortCommand) -> None:

        # Step 1 — cohort must exist and be active
        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))
        if not cohort.is_active():
            raise CohortArchivedError(str(command.cohort_id))

        # Step 2 — teacher must exist and be active
        teacher = self.teacher_repository.find_by_id(command.teacher_id)
        if teacher is None:
            raise TeacherNotFoundError(str(command.teacher_id))

        # Step 3 — teacher must not already be in this cohort
        if self.cohort_repository.teacher_in_cohort(
            command.cohort_id, command.teacher_id
        ):
            raise TeacherAlreadyInCohortError(
                str(command.teacher_id),
                str(command.cohort_id),
            )

        # Step 4 — assign
        self.cohort_repository.assign_teacher(
            command.cohort_id,
            command.teacher_id,
        )

        # Step 5 — publish event so Analytics knows
        self.event_publisher.publish_teacher_assigned_to_cohort(
            command.teacher_id,
            command.cohort_id,
        )