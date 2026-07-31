from application.ports.outbound.leaderboard_repository import (
    LeaderboardRepositoryPort,
)
from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.models import LeaderboardEntry


class RefreshLeaderboardUseCase:
    """
    Runs every 5 minutes via Celery (infrastructure/jobs/celery_app.py).

    Recalculates a single platform-wide rank by performance_score and
    rewrites the leaderboard table in one pass. Rank is computed
    globally rather than per-cohort: LeaderboardRepositoryPort exposes
    exactly one `rank` field, and find_global() / find_by_cohort() both
    just order by it -- find_by_cohort reads as "show me this cohort's
    students within the global ranking," not a separately-renumbered
    per-cohort leaderboard. This is the only place
    StudentAnalyticsModel.rank actually gets written -- everywhere else
    treats rank as read-only, per Rule 5 in the guide ("ranking
    calculations are expensive... only the final rank positions are
    periodic").

    NOTE: student_name / cohort_name aren't part of the StudentAnalytics
    domain model (no name-lookup port exists in this service), so
    they're placeholders below. Once student/cohort names are
    denormalized into this service (e.g. via a Kafka event or a
    lightweight lookup table), replace the placeholders with the real
    values.
    """

    def __init__(
        self,
        student_analytics_repository: StudentAnalyticsRepositoryPort,
        leaderboard_repository: LeaderboardRepositoryPort,
    ):
        self._student_analytics_repository = student_analytics_repository
        self._leaderboard_repository = leaderboard_repository

    def execute(self) -> None:
        all_students = self._student_analytics_repository.find_all()
        if not all_students:
            return

        ranked = sorted(
            all_students, key=lambda s: s.performance_score, reverse=True
        )

        entries: list[LeaderboardEntry] = []
        for position, student in enumerate(ranked, start=1):
            student.rank = position
            self._student_analytics_repository.save(student)

            if student.cohort_id is None:
                continue

            entries.append(
                LeaderboardEntry(
                    student_id=student.student_id,
                    student_name=f"Student {student.student_id}",
                    cohort_id=student.cohort_id,
                    cohort_name=f"Cohort {student.cohort_id}",
                    rank=position,
                    rating=student.rating,
                    performance_score=student.performance_score,
                    problem_solved_count=student.problem_solved_count,
                    consistency_score=student.consistency_score,
                )
            )

        self._leaderboard_repository.save_all(entries)