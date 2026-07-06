from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from domain.enums import (WarningStatus, WarningType)
@dataclass
class Warning:

    id: UUID
    student_id: UUID
    type: WarningType
    status: WarningStatus
    warning_number: int         # 1, 2, or 3
    issued_at: datetime
    dismissed_at: Optional[datetime]
    dismissed_by: Optional[UUID]
    dismissal_note: Optional[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_active(self) -> bool:
        return self.status == WarningStatus.ACTIVE

    def is_escalated(self) -> bool:
        """
        A warning is escalated when warning_number reaches 3.
        This triggers admin notification.
        """
        return self.warning_number >= 3