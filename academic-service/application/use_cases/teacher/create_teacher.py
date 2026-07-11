from dataclasses import dataclass
from uuid import uuid4, UUID

from domain.models import Teacher
from domain.exceptions import TeacherAlreadyExistsError
from domain.enums import TeacherStatus
from application.ports.outbound.teacher_repository import TeacherRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort

@dataclass
class CreateTeacherCommand:
    user_id: UUID
    full_name: str
    email: str
    
@dataclass
class CreateTeacherResult:
    teacher: Teacher

class CreateTeacherUseCase:
    def __init__(self, teacher_repository: TeacherRepositoryPort, event_publisher: EventPublisherPort):
        self.teacher_repository = teacher_repository
        self.event_publisher = event_publisher
        
    def execute(self, command: CreateTeacherCommand) -> CreateTeacherResult:
        if self.teacher_repository.exists_by_user_id(command.user_id):
            raise TeacherAlreadyExistsError(str(command.user_id))
        
        new_teacher = Teacher(
            id=uuid4(), 
            user_id=command.user_id, 
            full_name=command.full_name,
            email=command.email,
            status=TeacherStatus.PENDING
        )
        
        saved_teacher = self.teacher_repository.save(new_teacher)
        
        self.event_publisher.publish_teacher_created(saved_teacher)
        
        return CreateTeacherResult(teacher=saved_teacher)