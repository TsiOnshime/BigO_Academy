from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import Teacher
from domain.exceptions import TeacherNotFoundError
from application.ports.outbound.teacher_repository import TeacherRepositoryPort


@dataclass
class UpdateTeacherCommand:
    teacher_id: UUID
    full_name: Optional[str] = None
    email: Optional[str] = None


class UpdateTeacherUseCase:

    def __init__(self, teacher_repository: TeacherRepositoryPort):
        self.teacher_repository = teacher_repository

    def execute(self, command: UpdateTeacherCommand) -> Teacher:

        teacher = self.teacher_repository.find_by_id(command.teacher_id)
        if teacher is None:
            raise TeacherNotFoundError(str(command.teacher_id))

        if command.full_name is not None:
            teacher.full_name = command.full_name
        if command.email is not None:
            teacher.email = command.email

        return self.teacher_repository.save(teacher)