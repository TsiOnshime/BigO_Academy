from dataclasses import dataclass
from uuid import UUID

from typing import Optional

from domain.models import Student
from domain.exceptions import StudentNotFoundError
from application.ports.outbound.student_repository import StudentRepositoryPort

@dataclass
class UpdateStudentCommand:
    student_id: UUID
    full_name: Optional[str] = None
    email: Optional[str] = None

class UpdateStudentUseCase:
    def __init__(self, student_repository: StudentRepositoryPort):
        self.student_repository = student_repository
        
    def execute(self, command: UpdateStudentCommand) -> Student:
        student = self.student_repository.find_by_id(command.student_id)
        
        if student is None:
            raise StudentNotFoundError(str(command.student_id))
        if command.full_name is not None:
            student.full_name = command.full_name
        if command.email is not None:
            student.email = command.email
        
        return self.student_repository.save(student)
        
    