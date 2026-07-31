from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.models import ContestStats, StudentAnalytics

CLEAN_SOLVE_ATTEMPT_THRESHOLD = 2
CONSISTENCY_EMA_ALPHA = 0.3
PERFORMANCE_ATTENDANCE_WEIGHT = 0.4
PERFORMANCE_CONSISTENCY_WEIGHT = 0.4
PERFORMANCE_VOLUME_WEIGHT = 0.2
PERFORMANCE_VOLUME_CAP = 100


@dataclass
class ProcessProblemSolvedCommand:
    student_id: UUID
    problem_id: UUID
    attempts: int
    solve_time_minutes: float
    timestamp: Optional[str] = None


class ProcessProblemSolvedUseCase:
    """
    Kafka consumer target for: academic.problem.solved

    NOTE: the exact scoring formula (how attempts/solve-time roll up
    into consistency_score, and how that rolls up into
    performance_score) is a product/business decision this guide
    doesn't specify. The implementation below is a reasonable,
    self-contained heuristic -- swap in the real formula when it's
    defined without touching the port or the Kafka consumer.
    """

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(self, command: ProcessProblemSolvedCommand) -> None:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            analytics = self._new_student_analytics(command.student_id)

        analytics.problem_solved_count += 1

        is_clean_solve = command.attempts <= CLEAN_SOLVE_ATTEMPT_THRESHOLD
        if is_clean_solve:
            analytics.current_streak += 1
            analytics.longest_streak = max(
                analytics.longest_streak, analytics.current_streak
            )
        else:
            analytics.current_streak = 0

        efficiency = self._solve_efficiency(
            command.attempts, command.solve_time_minutes
        )
        analytics.consistency_score = round(
            analytics.consistency_score * (1 - CONSISTENCY_EMA_ALPHA)
            + efficiency * CONSISTENCY_EMA_ALPHA,
            2,
        )
        analytics.performance_score = self._recompute_performance_score(
            analytics
        )

        self._student_analytics_repository.save(analytics)

    @staticmethod
    def _solve_efficiency(attempts: int, solve_time_minutes: float) -> float:
        attempt_penalty = max(0, attempts - 1) * 15
        time_penalty = max(0.0, solve_time_minutes - 20) * 1.0
        return max(0.0, 100.0 - attempt_penalty - time_penalty)

    @staticmethod
    def _recompute_performance_score(analytics: StudentAnalytics) -> float:
        volume_component = min(
            analytics.problem_solved_count, PERFORMANCE_VOLUME_CAP
        )
        score = (
            analytics.attendance_percentage * PERFORMANCE_ATTENDANCE_WEIGHT
            + analytics.consistency_score * PERFORMANCE_CONSISTENCY_WEIGHT
            + volume_component * PERFORMANCE_VOLUME_WEIGHT
        )
        return round(score, 2)

    @staticmethod
    def _new_student_analytics(student_id: UUID) -> StudentAnalytics:
        return StudentAnalytics(
            student_id=student_id,
            cohort_id=None,
            rank=0,
            rating=0.0,
            performance_score=0.0,
            consistency_score=0.0,
            attendance_percentage=0.0,
            problem_solved_count=0,
            current_streak=0,
            longest_streak=0,
            active_warning_count=0,
            contest_stats=ContestStats(
                total_contests_participated=0,
                average_rank=0.0,
                best_rank=0,
                total_problems_solved_in_contests=0,
            ),
        )