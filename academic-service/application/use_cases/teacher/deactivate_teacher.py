from dataclasses import dataclass
from uuid import UUID

from domain.models import Teacher
from domain.enums import TeacherStatus
from domain.exceptions import TeacherNotFoundError
from application.ports.outbound.teacher_repository import TeacherRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class DeactivateTeacherCommand:
    teacher_id: UUID


class DeactivateTeacherUseCase:

    def __init__(
        self,
        teacher_repository: TeacherRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.teacher_repository = teacher_repository
        self.event_publisher = event_publisher

    def execute(self, command: DeactivateTeacherCommand) -> Teacher:

        teacher = self.teacher_repository.find_by_id(command.teacher_id)
        if teacher is None:
            teacher = self.teacher_repository.find_by_user_id(command.teacher_id)
        if teacher is None:
            raise TeacherNotFoundError(str(command.teacher_id))

        teacher.status = TeacherStatus.INACTIVE
        saved_teacher = self.teacher_repository.save(teacher)

        # Publish event so Analytics and Payment services know
        self.event_publisher.publish_teacher_status_changed(saved_teacher)

        return saved_teacher