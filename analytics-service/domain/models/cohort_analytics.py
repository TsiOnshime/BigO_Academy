from dataclasses import dataclass
from uuid import UUID

@dataclass
class WarningStats:
    total_issued: int
    total_resolved: int
    active_warnings: int
    students_on_probation: int

@dataclass
class ProgressionStats:
    promoted_to_year2: int
    graduated: int
    dropped: int
    active: int

@dataclass
class CohortAnalytics:
    cohort_id: UUID
    cohort_name: str
    total_students: int
    average_performance_score: float
    average_attendance_percentage: float
    average_consistency_score: float
    warning_stats: WarningStats
    progression_stats: ProgressionStats
    last_updated: str