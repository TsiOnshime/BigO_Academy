from dataclasses import dataclass
from uuid import UUID

from domain.models import Warning
from domain.exceptions import StudentNotFoundError
from application.ports.outbound.warning_repository import WarningRepositoryPort
from application.ports.outbound.student_repository import StudentRepositoryPort


@dataclass
class GetStudentWarningsCommand:
    student_id: UUID


@dataclass
class GetStudentWarningsResult:
    student_id: UUID
    active_warning_count: int
    warnings: list[Warning]


class GetStudentWarningsUseCase:

    def __init__(
        self,
        student_repository: StudentRepositoryPort,
        warning_repository: WarningRepositoryPort,
    ):
        self.student_repository = student_repository
        self.warning_repository = warning_repository

    def execute(
        self, command: GetStudentWarningsCommand
    ) -> GetStudentWarningsResult:

        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))

        warnings = self.warning_repository.find_by_student(command.student_id)
        active_count = self.warning_repository.count_active_warnings(
            command.student_id
        )

        return GetStudentWarningsResult(
            student_id=command.student_id,
            active_warning_count=active_count,
            warnings=warnings,
        )