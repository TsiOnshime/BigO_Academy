from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID
from typing import Optional

from domain.models import AttendanceRecord, ClassSession


class AttendanceRepositoryPort(ABC):

    @abstractmethod
    def save_session(self, session: ClassSession) -> ClassSession:
        """create or update attendance for a whole class session"""

    @abstractmethod
    def find_session_by_id(self, session_id: UUID) -> Optional[ClassSession]:
        """Fetch session with all its attendance records."""

    @abstractmethod
    def find_sessions_by_cohort(
        self, cohort_id: UUID, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[ClassSession]:
        """list class sessions for a cohort, optionally bounded by a date range"""

    @abstractmethod
    def find_student_attendance(
        self, student_id: UUID, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[AttendanceRecord]:
        """list attendance records for a student, optionally bounded by a date range"""

    @abstractmethod
    def calculate_attendance_percentage(self, student_id: UUID) -> float:
        """current overall attendance percentage for a student, computed via aggregation
        
        SQL aggregation query.
        Returns: (present_count / total_sessions) * 100
        More efficient than fetching all records and calculating in Python."""