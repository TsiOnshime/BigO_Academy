from dataclasses import dataclass
from typing import Optional


from domain.models import Teacher
from domain.enums import TeacherStatus
from application.ports.outbound.teacher_repository import TeacherRepositoryPort

@dataclass
class ListTeachersCommand:
    status: Optional[TeacherStatus] = None

class ListTeachersUseCase:
    def __init__(self, teacher_repository: TeacherRepositoryPort):
        self.teacher_repository = teacher_repository
    
    def execute(self, command: ListTeachersCommand) -> list[Teacher]:
        return self.teacher_repository.find_all(status=command.status)

