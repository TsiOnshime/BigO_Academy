from dataclasses import dataclass
from uuid import UUID

from domain.models import Teacher
from domain.exceptions import TeacherNotFoundError
from application.ports.outbound.teacher_repository import TeacherRepositoryPort

@dataclass
class GetTeacherCommand:
    teacher_id: UUID
    
class GetTeacherUseCase:
    def __init__(self, teacher_repository: TeacherRepositoryPort):
        self.teacher_repository = teacher_repository
    
    def execute(self, command: GetTeacherCommand) -> Teacher:
        teacher = self.teacher_repository.find_by_id(command.teacher_id)
        
        if teacher is None:
            raise TeacherNotFoundError(str(command.teacher_id))
        return teacher
    


