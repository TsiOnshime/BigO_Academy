from dataclasses import dataclass, field
from uuid import UUID
from domain.enums import (CohortStatus)
from typing import Optional
from datetime import date, datetime, timezone
@dataclass
class Cohort:
    id: UUID
    name: str
    status: CohortStatus
    intake_window_one: Optional[date]
    intake_window_two: Optional[date]
    start_date: date
    expected_graduation_date: date
    student_capacity: int
    enrolled_student_count: int
    teacher_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_active(self) -> bool:
        return self.status == CohortStatus.ACTIVE
    def is_at_capacity(self) -> bool:
        return self.enrolled_student_count >= self.student_capacity
    