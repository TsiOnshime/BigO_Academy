from dataclasses import dataclass
from uuid import UUID

from domain.models import MentorshipSession
from domain.exceptions import MentorshipSessionNotFoundError
from application.ports.outbound.mentorship_repository import MentorshipRepositoryPort


@dataclass
class GetMentorshipSessionCommand:
    session_id: UUID


class GetMentorshipSessionUseCase:

    def __init__(self, mentorship_repository: MentorshipRepositoryPort):
        self.mentorship_repository = mentorship_repository

    def execute(self, command: GetMentorshipSessionCommand) -> MentorshipSession:

        session = self.mentorship_repository.find_by_id(command.session_id)
        if session is None:
            raise MentorshipSessionNotFoundError(str(command.session_id))

        return session