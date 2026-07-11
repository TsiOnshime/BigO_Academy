from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from domain.enums import StudentStatus
from domain.models import Student
from application.ports.outbound.student_repository import StudentRepositoryPort

@dataclass
class ListStudentsCommand:
    cohort_id: Optional[UUID] = None
    status: Optional[StudentStatus] = None


class ListStudentsUseCase:
    def __init__(self, student_repository: StudentRepositoryPort):
        self.student_repository = student_repository
    
    def execute(self, command: ListStudentsCommand) -> list[Student]:
        return self.student_repository.find_all(cohort_id=command.cohort_id, status=command.status)
    