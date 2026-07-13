from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime, date, timezone

from domain.enums import (TeacherStatus)
@dataclass
class Teacher:
    id: UUID
    user_id: UUID
    full_name: str
    email: str
    status: TeacherStatus
    assigned_cohort_ids: list[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    
    def is_active(self) -> bool:
        return self.status == TeacherStatus.ACTIVE
    def is_assigned_to_cohort(self, cohort_id: UUID) -> bool:
        return cohort_id in self.assigned_cohort_ids
    