from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional

from domain.models import MentorshipSession
from domain.enums import MentorshipSessionStatus
from domain.exceptions import MentorshipSessionNotFoundError
from application.ports.outbound.mentorship_repository import MentorshipRepositoryPort


@dataclass
class UpdateMentorshipSessionCommand:
    session_id: UUID
    scheduled_at: Optional[datetime] = None
    status: Optional[MentorshipSessionStatus] = None
    notes: Optional[str] = None


class UpdateMentorshipSessionUseCase:

    def __init__(self, mentorship_repository: MentorshipRepositoryPort):
        self.mentorship_repository = mentorship_repository

    def execute(self, command: UpdateMentorshipSessionCommand) -> MentorshipSession:

        session = self.mentorship_repository.find_by_id(command.session_id)
        if session is None:
            raise MentorshipSessionNotFoundError(str(command.session_id))

        if command.scheduled_at is not None:
            session.scheduled_at = command.scheduled_at
        if command.status is not None:
            session.status = command.status
        if command.notes is not None:
            session.notes = command.notes

        return self.mentorship_repository.save(session)