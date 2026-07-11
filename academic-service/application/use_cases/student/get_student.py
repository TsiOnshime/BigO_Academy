from dataclasses import dataclass
from uuid import UUID

from domain.models import Student
from domain.exceptions import StudentNotFoundError

from application.ports.outbound.student_repository import StudentRepositoryPort

@dataclass
class GetStudentCommand:
    student_id: UUID

class GetStudentUseCase:
    def __init__(self, student_repository: StudentRepositoryPort):
        self.student_repository = student_repository
    
    def execute(self, command: GetStudentCommand) -> Student:
        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))
        return student