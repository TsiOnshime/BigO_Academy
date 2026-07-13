from dataclasses import dataclass
from uuid import UUID

from domain.models import ClassSession
from domain.exceptions import SessionNotFoundError
from application.ports.outbound.attendance_repository import AttendanceRepositoryPort


@dataclass
class GetSessionAttendanceCommand:
    session_id: UUID


class GetSessionAttendanceUseCase:

    def __init__(self, attendance_repository: AttendanceRepositoryPort):
        self.attendance_repository = attendance_repository

    def execute(self, command: GetSessionAttendanceCommand) -> ClassSession:

        session = self.attendance_repository.find_session_by_id(command.session_id)
        if session is None:
            raise SessionNotFoundError(str(command.session_id))

        return session