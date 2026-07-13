from dataclasses import dataclass
from uuid import UUID

from domain.models import ClassSession, AttendanceRecord
from domain.enums import AttendanceStatus
from domain.exceptions import SessionNotFoundError
from application.ports.outbound.attendance_repository import AttendanceRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class AttendanceEditInput:
    student_id: UUID
    status: AttendanceStatus
    note: str = None


@dataclass
class EditAttendanceCommand:
    session_id: UUID
    records: list[AttendanceEditInput]


class EditAttendanceUseCase:

    def __init__(
        self,
        attendance_repository: AttendanceRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.attendance_repository = attendance_repository
        self.event_publisher = event_publisher

    def execute(self, command: EditAttendanceCommand) -> ClassSession:

        session = self.attendance_repository.find_session_by_id(command.session_id)
        if session is None:
            raise SessionNotFoundError(str(command.session_id))

        # Update records
        updated_records = {r.student_id: r for r in command.records}
        for record in session.records:
            if record.student_id in updated_records:
                edit = updated_records[record.student_id]
                record.status = edit.status
                record.note = edit.note

        # Recalculate counts
        session.present_count = sum(
            1 for r in session.records if r.status == AttendanceStatus.PRESENT
        )
        session.absent_count = sum(
            1 for r in session.records if r.status == AttendanceStatus.ABSENT
        )
        session.excused_count = sum(
            1 for r in session.records if r.status == AttendanceStatus.EXCUSED
        )

        saved_session = self.attendance_repository.save_session(session)

        # Publish updated events for changed records
        for record in command.records:
            self.event_publisher.publish_attendance_updated(
                student_id=record.student_id,
                session_id=saved_session.id,
                status=record.status.value,
            )

        return saved_session