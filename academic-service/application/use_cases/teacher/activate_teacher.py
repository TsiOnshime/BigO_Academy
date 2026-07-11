from dataclasses import dataclass
from uuid import UUID

from domain.models import Teacher
from domain.enums import TeacherStatus
from domain.exceptions import TeacherNotFoundError
from application.ports.outbound.teacher_repository import TeacherRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class ActivateTeacherCommand:
    teacher_id: UUID


class ActivateTeacherUseCase:

    def __init__(
        self,
        teacher_repository: TeacherRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.teacher_repository = teacher_repository
        self.event_publisher = event_publisher

    def execute(self, command: ActivateTeacherCommand) -> Teacher:

        teacher = self.teacher_repository.find_by_id(command.teacher_id)
        if teacher is None:
            raise TeacherNotFoundError(str(command.teacher_id))

        # Idempotent — activating an already active teacher is harmless
        teacher.status = TeacherStatus.ACTIVE
        saved_teacher = self.teacher_repository.save(teacher)

        self.event_publisher.publish_teacher_status_changed(saved_teacher)

        return saved_teacher