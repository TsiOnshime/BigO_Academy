from dataclasses import dataclass
from uuid import UUID

@dataclass
class LeaderboardEntry:
    student_id: UUID
    student_name: str
    cohort_id: UUID
    cohort_name: str
    rank: int
    rating: float
    performance_score: float
    problem_solved_count: int
    consistency_score: float