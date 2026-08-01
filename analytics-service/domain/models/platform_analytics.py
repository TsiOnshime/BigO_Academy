from dataclasses import dataclass

@dataclass
class PlatformAnalytics:
    total_students: int
    total_teachers: int
    total_active_cohorts: int
    total_archived_cohorts: int
    overall_average_performance_score: float
    overall_average_attendance_percentage: float
    total_warnings_issued: int
    students_on_probation: int
    students_dropped: int
    total_graduates: int
    last_updated: str