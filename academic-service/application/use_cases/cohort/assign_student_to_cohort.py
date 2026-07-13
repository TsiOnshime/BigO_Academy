from dataclasses import dataclass
from uuid import UUID

from domain.exceptions import (
    CohortNotFoundError,
    StudentNotFoundError,
    StudentAlreadyInCohortError,
    CohortArchivedError,
)
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.student_repository import StudentRepositoryPort


@dataclass
class AssignStudentToCohortCommand:
    cohort_id: UUID
    student_id: UUID


class AssignStudentToCohortUseCase:

    def __init__(
        self,
        cohort_repository: CohortRepositoryPort,
        student_repository: StudentRepositoryPort,
    ):
        self.cohort_repository = cohort_repository
        self.student_repository = student_repository

    def execute(self, command: AssignStudentToCohortCommand) -> None:

        # Step 1 — cohort must exist and be active
        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))
        if not cohort.is_active():
            raise CohortArchivedError(str(command.cohort_id))

        # Step 2 — student must exist
        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))

        # Step 3 — student must not already be in this cohort
        if self.cohort_repository.student_in_cohort(
            command.cohort_id, command.student_id
        ):
            raise StudentAlreadyInCohortError(
                str(command.student_id),
                str(command.cohort_id),
            )

        # Step 4 — assign
        self.cohort_repository.assign_student(
            command.cohort_id,
            command.student_id,
        )