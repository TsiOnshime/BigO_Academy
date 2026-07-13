from dataclasses import dataclass
from uuid import UUID

from domain.models import Student
from domain.enums import StudentStatus
from domain.exceptions import (
    StudentNotFoundError,
    StudentNotEligibleForGraduationError,
)
from application.ports.outbound.student_repository import StudentRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class GraduateStudentCommand:
    student_id: UUID


class GraduateStudentUseCase:

    def __init__(
        self,
        student_repository: StudentRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.student_repository = student_repository
        self.event_publisher = event_publisher

    def execute(self, command: GraduateStudentCommand) -> Student:

        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))

        if not student.is_eligible_for_graduation():
            raise StudentNotEligibleForGraduationError(
                student_id=str(command.student_id),
                reason=(
                    "Student must be in Year 2 and ACTIVE status "
                    f"(current: Year {student.year_phase.value}, {student.status.value})"
                ),
            )

        student.status = StudentStatus.GRADUATED
        saved_student = self.student_repository.save(student)

        self.event_publisher.publish_student_graduated(saved_student)

        return saved_student