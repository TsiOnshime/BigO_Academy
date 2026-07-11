from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import MentorshipSession
from application.ports.outbound.mentorship_repository import MentorshipRepositoryPort


@dataclass
class ListMentorshipSessionsCommand:
    student_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None


class ListMentorshipSessionsUseCase:

    def __init__(self, mentorship_repository: MentorshipRepositoryPort):
        self.mentorship_repository = mentorship_repository

    def execute(
        self, command: ListMentorshipSessionsCommand
    ) -> list[MentorshipSession]:

        if command.student_id is not None:
            return self.mentorship_repository.find_by_student(command.student_id)

        if command.teacher_id is not None:
            return self.mentorship_repository.find_by_teacher(command.teacher_id)

        # If neither filter provided return empty — avoids fetching everything
        return []