from dataclasses import dataclass
from datetime import date
from uuid import uuid4, UUID

from domain.models import ClassSession, AttendanceRecord
from domain.enums import AttendanceStatus
from domain.exceptions import CohortNotFoundError
from application.ports.outbound.attendance_repository import AttendanceRepositoryPort
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class AttendanceRecordInput:
    student_id: UUID
    status: AttendanceStatus
    note: str = None


@dataclass
class SubmitAttendanceCommand:
    cohort_id: UUID
    session_date: date
    records: list[AttendanceRecordInput]


class SubmitAttendanceUseCase:

    def __init__(
        self,
        attendance_repository: AttendanceRepositoryPort,
        cohort_repository: CohortRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.attendance_repository = attendance_repository
        self.cohort_repository = cohort_repository
        self.event_publisher = event_publisher

    def execute(self, command: SubmitAttendanceCommand) -> ClassSession:

        # Cohort must exist
        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))

        # Build attendance records
        records = [
            AttendanceRecord(
                student_id=r.student_id,
                status=r.status,
                note=r.note,
            )
            for r in command.records
        ]

        # Calculate counts
        present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)

        session = ClassSession(
            id=uuid4(),
            cohort_id=command.cohort_id,
            session_date=command.session_date,
            total_students=len(records),
            present_count=present,
            absent_count=absent,
            excused_count=excused,
            records=records,
        )

        saved_session = self.attendance_repository.save_session(session)

        # Publish AttendanceUpdated event for each student
        for record in records:
            self.event_publisher.publish_attendance_updated(
                student_id=record.student_id,
                session_id=saved_session.id,
                status=record.status.value,
            )

        return saved_session