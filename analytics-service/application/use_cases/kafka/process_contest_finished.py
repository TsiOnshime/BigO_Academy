from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from application.ports.outbound.cohort_analytics_repository import (
    CohortAnalyticsRepositoryPort,
)
from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.models import (
    CohortAnalytics,
    ContestStats,
    ProgressionStats,
    StudentAnalytics,
    WarningStats,
)

RATING_BASELINE_RANK = 50
RATING_K_FACTOR = 0.5


@dataclass
class ProcessContestFinishedCommand:
    contest_id: UUID
    cohort_id: UUID
    results: list[dict]
    timestamp: Optional[str] = None


class ProcessContestFinishedUseCase:
    """
    Kafka consumer target for: academic.contest.finished

    Expected shape of each entry in `results` (camelCase, matching the
    Academic Service's event payload convention used elsewhere in the
    guide): {"studentId": str, "rank": int, "problemsSolved": int}.

    NOTE: the rating adjustment below is a simple placeholder --
    a fixed baseline-rank comparison rather than a real Elo/Glicko
    system. Swap in the real rating algorithm once defined.
    """

    def __init__(
        self,
        student_analytics_repository: StudentAnalyticsRepositoryPort,
        cohort_analytics_repository: CohortAnalyticsRepositoryPort,
    ):
        self._student_analytics_repository = student_analytics_repository
        self._cohort_analytics_repository = cohort_analytics_repository

    def execute(self, command: ProcessContestFinishedCommand) -> None:
        for result in command.results:
            self._apply_result_to_student(command.cohort_id, result)

        self._refresh_cohort_averages(command.cohort_id)

    def _apply_result_to_student(self, cohort_id: UUID, result: dict) -> None:
        student_id = UUID(str(result["studentId"]))
        contest_rank = int(result["rank"])
        problems_solved = int(result.get("problemsSolved", 0))

        analytics = self._student_analytics_repository.find_by_student_id(
            student_id
        )
        if analytics is None:
            analytics = self._new_student_analytics(student_id, cohort_id)

        stats = analytics.contest_stats
        previous_total = stats.total_contests_participated
        new_total = previous_total + 1

        new_average_rank = round(
            (stats.average_rank * previous_total + contest_rank)
            / new_total,
            2,
        )
        new_best_rank = (
            contest_rank
            if previous_total == 0
            else min(stats.best_rank, contest_rank)
        )

        analytics.contest_stats = ContestStats(
            total_contests_participated=new_total,
            average_rank=new_average_rank,
            best_rank=new_best_rank,
            total_problems_solved_in_contests=(
                stats.total_problems_solved_in_contests + problems_solved
            ),
        )
        analytics.rating = max(
            0.0,
            round(
                analytics.rating
                + (RATING_BASELINE_RANK - contest_rank) * RATING_K_FACTOR,
                2,
            ),
        )

        self._student_analytics_repository.save(analytics)

    def _refresh_cohort_averages(self, cohort_id: UUID) -> None:
        """
        Recompute the cohort's rolled-up averages after contest ratings
        change. Warning/progression stats are left untouched here since
        this event has nothing to do with warnings or promotions.
        """
        students = self._student_analytics_repository.find_all_by_cohort(
            cohort_id
        )
        if not students:
            return

        existing = self._cohort_analytics_repository.find_by_cohort_id(
            cohort_id
        )

        total = len(students)
        avg_performance = round(
            sum(s.performance_score for s in students) / total, 2
        )
        avg_attendance = round(
            sum(s.attendance_percentage for s in students) / total, 2
        )
        avg_consistency = round(
            sum(s.consistency_score for s in students) / total, 2
        )

        updated = CohortAnalytics(
            cohort_id=cohort_id,
            cohort_name=existing.cohort_name if existing else "Unknown Cohort",
            total_students=total,
            average_performance_score=avg_performance,
            average_attendance_percentage=avg_attendance,
            average_consistency_score=avg_consistency,
            warning_stats=(
                existing.warning_stats
                if existing
                else WarningStats(0, 0, 0, 0)
            ),
            progression_stats=(
                existing.progression_stats
                if existing
                else ProgressionStats(0, 0, 0, total)
            ),
            last_updated="",  # ORM sets this via auto_now on save
        )
        self._cohort_analytics_repository.save(updated)

    @staticmethod
    def _new_student_analytics(
        student_id: UUID, cohort_id: UUID
    ) -> StudentAnalytics:
        return StudentAnalytics(
            student_id=student_id,
            cohort_id=cohort_id,
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