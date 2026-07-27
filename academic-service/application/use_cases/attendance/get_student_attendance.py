from dataclasses import dataclass
from datetime import date
from uuid import UUID
from typing import Optional

from domain.models import AttendanceRecord
from domain.exceptions import StudentNotFoundError
from application.ports.outbound.attendance_repository import AttendanceRepositoryPort
from application.ports.outbound.student_repository import StudentRepositoryPort


@dataclass
class GetStudentAttendanceCommand:
    student_id: UUID
    from_date: Optional[date] = None
    to_date: Optional[date] = None


@dataclass
class GetStudentAttendanceResult:
    student_id: UUID
    attendance_percentage: float
    total_sessions: int
    present_count: int
    absent_count: int
    excused_count: int
    history: list[AttendanceRecord]


class GetStudentAttendanceUseCase:

    def __init__(
        self,
        student_repository: StudentRepositoryPort,
        attendance_repository: AttendanceRepositoryPort,
    ):
        self.student_repository = student_repository
        self.attendance_repository = attendance_repository

    def execute(
        self, command: GetStudentAttendanceCommand
    ) -> GetStudentAttendanceResult:

        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))

        history = self.attendance_repository.find_student_attendance(
            student_id=command.student_id,
            from_date=command.from_date,
            to_date=command.to_date,
        )

        percentage = self.attendance_repository.calculate_attendance_percentage(
            command.student_id
        )

        present = sum(1 for r in history if r.status.value == "PRESENT")
        absent = sum(1 for r in history if r.status.value == "ABSENT")
        excused = sum(1 for r in history if r.status.value == "EXCUSED")

        return GetStudentAttendanceResult(
            student_id=command.student_id,
            attendance_percentage=percentage,
            total_sessions=len(history),
            present_count=present,
            absent_count=absent,
            excused_count=excused,
            history=history,
        )