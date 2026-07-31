from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID
from domain.enums import ReportType

@dataclass
class AnalyticsReport:
    id: UUID
    report_type: ReportType
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    data: dict = field(default_factory=dict)