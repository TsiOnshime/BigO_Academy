from dataclasses import dataclass
from uuid import UUID

@dataclass
class StudentAtRisk:
    student_id: UUID
    student_name: str
    risk_reasons: list[str]
    attendance_percentage: float
    performance_score: float
    active_warning_count: int

@dataclass
class TopPerformer:
    student_id: UUID
    student_name: str
    rank: int
    performance_score: float
    problem_solved_count: int

@dataclass
class TeacherAnalytics:
    teacher_id: UUID
    assigned_cohort_count: int
    total_assigned_students: int
    students_at_risk: list[StudentAtRisk]
    top_performers: list[TopPerformer]
    last_updated: str