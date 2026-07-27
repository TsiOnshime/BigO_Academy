from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import UUID
from typing import Optional

from domain.enums import (ContestStatus)

@dataclass
class ContestResult:
    student_id: UUID
    student_name: str
    contest_rank: int
    problems_solved: int
    participated: bool
    
@dataclass
class Contest:

    id: UUID
    title: str
    cohort_id: UUID
    external_contest_url: str
    status: ContestStatus
    scheduled_at: datetime
    ended_at: Optional[datetime]
    problem_count: int
    results: list[ContestResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_finished(self) -> bool:
        return self.status == ContestStatus.FINISHED

    def has_results(self) -> bool:
        return len(self.results) > 0