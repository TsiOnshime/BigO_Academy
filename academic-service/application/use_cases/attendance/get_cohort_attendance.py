from dataclasses import dataclass
from datetime import date
from uuid import UUID
from typing import Optional

from domain.models import ClassSession
from domain.exceptions import CohortNotFoundError
from application.ports.outbound.attendance_repository import AttendanceRepositoryPort
from application.ports.outbound.cohort_repository import CohortRepositoryPort


@dataclass
class GetCohortAttendanceCommand:
    cohort_id: UUID
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class GetCohortAttendanceUseCase:

    def __init__(
        self,
        cohort_repository: CohortRepositoryPort,
        attendance_repository: AttendanceRepositoryPort,
    ):
        self.cohort_repository = cohort_repository
        self.attendance_repository = attendance_repository

    def execute(
        self, command: GetCohortAttendanceCommand
    ) -> list[ClassSession]:

        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))

        return self.attendance_repository.find_sessions_by_cohort(
            cohort_id=command.cohort_id,
            from_date=command.from_date,
            to_date=command.to_date,
        )