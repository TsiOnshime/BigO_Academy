from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID
from typing import Optional
from domain.enums import MetricType

@dataclass
class HistoricalMetric:
    id: UUID
    student_id: UUID
    snapshot_date: date
    rank: int
    rating: float
    performance_score: float
    consistency_score: float
    attendance_percentage: float
    problem_solved_count: int = 0