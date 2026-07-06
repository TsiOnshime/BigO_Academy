from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import UUID
from typing import Optional

from domain.enums import (MentorshipSessionStatus)

@dataclass
class MentorshipSession:
    id: UUID
    teacher_id: UUID
    student_id: UUID
    scheduled_at: datetime
    status: MentorshipSessionStatus
    notes: Optional[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_completed(self) -> bool:
        return self.status == MentorshipSessionStatus.COMPLETED

    def can_be_cancelled(self) -> bool:
        return self.status == MentorshipSessionStatus.SCHEDULED