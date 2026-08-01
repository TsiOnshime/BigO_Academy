from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from domain.models import StudentAnalytics, ContestStats
from application.ports.outbound.student_analytics_repository import StudentAnalyticsRepositoryPort

from core.models import StudentAnalyticsModel

class DjangoStudentAnalyticsRepository(StudentAnalyticsRepositoryPort):
    def _to_domain(self, orm: StudentAnalyticsModel) -> StudentAnalytics:
        return StudentAnalytics(
            student_id=orm.student_id,
            cohort_id=orm.cohort_id,
            rank=orm.rank,
            rating=orm.rating,
            performance_score=orm.performance_score,
            consistency_score=orm.consistency_score,
            attendance_percentage=orm.attendance_percentage,
            problem_solved_count=orm.problem_solved_count,
            current_streak=orm.current_streak,
            longest_streak=orm.longest_streak,
            active_warning_count=orm.active_warning_count,
            contest_stats=ContestStats(
                total_contests_participated=orm.total_contests_participated,
                average_rank=orm.average_contest_rank,
                best_rank=orm.best_contest_rank,
                total_problems_solved_in_contests=orm.total_problems_in_contests
            ),
            last_updated=orm.last_updated,
        )
    
    def _to_orm_fields(self, analytics: StudentAnalytics) -> dict:
        return {
            "cohort_id": analytics.cohort_id,
            "rank": analytics.rank,
            "rating": analytics.rating,
            "performance_score": analytics.performance_score,
            "consistency_score": analytics.consistency_score,
            "attendance_percentage": analytics.attendance_percentage,
            "problem_solved_count": analytics.problem_solved_count,
            "current_streak": analytics.current_streak,
            "longest_streak": analytics.longest_streak,
            "active_warning_count": analytics.active_warning_count,
            "total_contests_participated": analytics.contest_stats.total_contests_participated,
            "average_contest_rank": analytics.contest_stats.average_rank,
            "best_contest_rank": analytics.contest_stats.best_rank,
            "total_problems_in_contests": analytics.contest_stats.total_problems_solved_in_contests
        
        }
    def save(self, analytics: StudentAnalytics) -> StudentAnalytics:
        orm, _ = StudentAnalyticsModel.objects.update_or_create(student_id=analytics.student_id, defaults=self._to_orm_fields(analytics))
        
        return self._to_domain(orm)
    
    def find_by_student_id(self, student_id: UUID) -> Optional[StudentAnalytics]:
        try:
            return self._to_domain(
                StudentAnalyticsModel.objects.get(student_id=student_id)
            )
        except StudentAnalyticsModel.DoesNotExist:
            return None
    def find_all_by_cohort(self, cohort_id: UUID) -> list[StudentAnalytics]:
        queryset = StudentAnalyticsModel.objects.filter(cohort_id=cohort_id)
        return [self._to_domain(orm) for orm in queryset]

    def find_all(self) -> list[StudentAnalytics]:
        queryset = StudentAnalyticsModel.objects.all()
        return [self._to_domain(orm) for orm in queryset]
    
    def find_top_performers(self, cohort_id: UUID, limit: int = 10) -> list[StudentAnalytics]:
        queryset = StudentAnalyticsModel.objects.filter(cohort_id=cohort_id).order_by("-performance_score")[:limit]
        
        return [self._to_domain(orm) for orm in queryset]
    
    def find_at_risk(self, cohort_id: UUID) -> list[StudentAnalytics]:
        from django.db.models import Q
        queryset = StudentAnalyticsModel.objects.filter(cohort_id=cohort_id).filter(
            Q(attendance_percentage__lt=60.0) |
            Q(performance_score__lt==40) |
            Q(active_warning_count__gte=1))
        
        return [self._to_domain(orm) for orm in queryset]