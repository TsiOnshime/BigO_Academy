from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import UUID
from typing import Optional

from domain.enums import (AttendanceStatus)

@dataclass
class AttendanceRecord:
    student_id: UUID
    status: AttendanceStatus
    note: Optional[str] 
    
@dataclass
class ClassSession:
    id: UUID
    cohort_id: UUID
    session_date: date
    total_students: int
    present_count: int
    absent_count: int
    excused_count: int
    records: list[AttendanceRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def attendance_percentage(self) -> float:
        """
        Calculate attendance percentage for this session.
        Excused absences don't count against students.
        """
        if self.total_students == 0:
            return 0.0
        return round((self.present_count / self.total_students) * 100, 2)