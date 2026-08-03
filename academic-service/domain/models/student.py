from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from uuid import UUID
from typing import Optional 

from domain.enums import (StudentStatus,YearPhase)

@dataclass
class Student:
    id: UUID
    user_id: UUID
    full_name: str
    email: str
    cohort_id: Optional[UUID]
    year_phase: YearPhase
    status: StudentStatus
    assigned_teacher_id: Optional[UUID]
    attendance_percentage: float
    active_warning_count: int
    joined_at: date
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    
    def is_active(self) -> bool:
        return self.status == StudentStatus.ACTIVE
    def is_eligible_for_promotion(self) -> bool:
        return (self.year_phase == YearPhase.YEAR_ONE and self.status == StudentStatus.ACTIVE)
    def is_eligible_for_graduation(self) -> bool:
        return (self.year_phase == YearPhase.YEAR_TWO and self.status == StudentStatus.ACTIVE)
    def can_transition_to(self, new_status: StudentStatus) -> bool:
        """
        Enforces the valid status transitions:
        ACTIVE → PROBATION
        PROBATION → DROPPED
        PROBATION -> ACTIVE
        ACTIVE → GRADUATED
        Any → ARCHIVED
        """
        if new_status == StudentStatus.ARCHIVED:
            return True
        valid_transitions = {
            StudentStatus.ACTIVE: [StudentStatus.PROBATION, StudentStatus.GRADUATED],
            StudentStatus.PROBATION: [StudentStatus.DROPPED, StudentStatus.ACTIVE],
            StudentStatus.DROPPED: [],
            StudentStatus.GRADUATED: [],
            StudentStatus.ARCHIVED: [],
        }
        return new_status in valid_transitions.get(self.status, [])