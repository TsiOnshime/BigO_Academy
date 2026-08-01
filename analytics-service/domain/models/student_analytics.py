from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

@dataclass
class ContestStats:
    total_contests_participated: int
    average_rank: float
    best_rank: int
    total_problems_solved_in_contests: int

@dataclass
class StudentAnalytics:
    student_id: UUID
    cohort_id: Optional[UUID]
    rank: int
    rating: float
    performance_score: float
    consistency_score: float
    attendance_percentage: float
    problem_solved_count: int
    current_streak: int
    longest_streak: int
    active_warning_count: int
    contest_stats: ContestStats
    last_updated: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )