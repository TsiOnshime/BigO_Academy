from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.enums import StudentStatus
from domain.models import Student
from domain.exceptions import StudentNotFoundError, InvalidStudentStatusTransitionError
from application.ports.outbound.student_repository import StudentRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort

@dataclass
class UpdateStudentStatusCommand:
    student_id: UUID
    new_status: StudentStatus
    reason: Optional[str] = None

class UpdateStudentStatusUseCase:
    def __init__(self, student_repository: StudentRepositoryPort, event_publisher: EventPublisherPort):
        self.student_repository = student_repository
        self.event_publisher = event_publisher
    
    def execute(self, command: UpdateStudentStatusCommand) -> Student:
        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))
        if not student.can_transition_to(command.new_status):
            raise InvalidStudentStatusTransitionError(current_status=student.status.value, target_status=command.new_status.value)
        old_status = student.status
        student.status = command.new_status
        saved_student = self.student_repository.save(student)
        
        # Publish events based on transitions
        if command.new_status == StudentStatus.DROPPED:
            self.event_publisher.publish_student_dropped(saved_student)
        elif command.new_status == StudentStatus.GRADUATED:
            self.event_publisher.publish_student_graduated(saved_student)
        else:
            self.event_publisher.publish_student_status_changed(saved_student, old_status.value)
        return saved_student