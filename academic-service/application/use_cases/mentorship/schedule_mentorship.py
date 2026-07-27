from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4, UUID

from domain.models import MentorshipSession
from domain.enums import MentorshipSessionStatus
from domain.exceptions import StudentNotFoundError, TeacherNotFoundError
from application.ports.outbound.mentorship_repository import MentorshipRepositoryPort
from application.ports.outbound.student_repository import StudentRepositoryPort
from application.ports.outbound.teacher_repository import TeacherRepositoryPort


@dataclass
class ScheduleMentorshipCommand:
    teacher_id: UUID
    student_id: UUID
    scheduled_at: datetime


class ScheduleMentorshipUseCase:

    def __init__(
        self,
        mentorship_repository: MentorshipRepositoryPort,
        student_repository: StudentRepositoryPort,
        teacher_repository: TeacherRepositoryPort,
    ):
        self.mentorship_repository = mentorship_repository
        self.student_repository = student_repository
        self.teacher_repository = teacher_repository

    def execute(self, command: ScheduleMentorshipCommand) -> MentorshipSession:

        # Both teacher and student must exist
        teacher = self.teacher_repository.find_by_id(command.teacher_id)
        if teacher is None:
            raise TeacherNotFoundError(str(command.teacher_id))

        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))

        new_session = MentorshipSession(
            id=uuid4(),
            teacher_id=command.teacher_id,
            student_id=command.student_id,
            scheduled_at=command.scheduled_at,
            status=MentorshipSessionStatus.SCHEDULED,
            notes=None,
        )

        return self.mentorship_repository.save(new_session)