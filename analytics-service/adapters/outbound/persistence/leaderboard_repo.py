from uuid import UUID
from datetime import datetime, timezone

from domain.models import LeaderboardEntry
from application.ports.outbound.leaderboard_repository import (
    LeaderboardRepositoryPort,
)
from core.models import LeaderboardEntryModel


class DjangoLeaderboardRepository(LeaderboardRepositoryPort):

    def _to_domain(self, orm: LeaderboardEntryModel) -> LeaderboardEntry:
        return LeaderboardEntry(
            student_id=orm.student_id,
            student_name=orm.student_name,
            cohort_id=orm.cohort_id,
            cohort_name=orm.cohort_name,
            rank=orm.rank,
            rating=orm.rating,
            performance_score=orm.performance_score,
            problem_solved_count=orm.problem_solved_count,
            consistency_score=orm.consistency_score,
        )

    def save_entry(self, entry: LeaderboardEntry) -> LeaderboardEntry:
        orm, _ = LeaderboardEntryModel.objects.update_or_create(
            student_id=entry.student_id,
            cohort_id=entry.cohort_id,
            defaults={
                "student_name": entry.student_name,
                "cohort_name": entry.cohort_name,
                "rank": entry.rank,
                "rating": entry.rating,
                "performance_score": entry.performance_score,
                "problem_solved_count": entry.problem_solved_count,
                "consistency_score": entry.consistency_score,
            },
        )
        return self._to_domain(orm)

    def save_all(self, entries: list[LeaderboardEntry]) -> None:
        # Delete existing and bulk create for efficiency
        if not entries:
            return

        cohort_ids = {e.cohort_id for e in entries}

        LeaderboardEntryModel.objects.filter(
            cohort_id__in=cohort_ids
        ).delete()

        LeaderboardEntryModel.objects.bulk_create(
            [
                LeaderboardEntryModel(
                    student_id=e.student_id,
                    student_name=e.student_name,
                    cohort_id=e.cohort_id,
                    cohort_name=e.cohort_name,
                    rank=e.rank,
                    rating=e.rating,
                    performance_score=e.performance_score,
                    problem_solved_count=e.problem_solved_count,
                    consistency_score=e.consistency_score,
                )
                for e in entries
            ]
        )

    def find_global(
        self,
        page: int = 0,
        size: int = 20,
    ) -> list[LeaderboardEntry]:
        offset = page * size

        queryset = LeaderboardEntryModel.objects.order_by(
            "rank"
        )[offset : offset + size]

        return [self._to_domain(orm) for orm in queryset]

    def find_by_cohort(
        self,
        cohort_id: UUID,
        page: int = 0,
        size: int = 20,
    ) -> list[LeaderboardEntry]:
        offset = page * size

        queryset = (
            LeaderboardEntryModel.objects.filter(
                cohort_id=cohort_id
            )
            .order_by("rank")[offset : offset + size]
        )

        return [self._to_domain(orm) for orm in queryset]

    def get_last_refreshed(self) -> str:
        latest = (
            LeaderboardEntryModel.objects.order_by(
                "-calculated_at"
            ).first()
        )

        if latest:
            return latest.calculated_at.isoformat()

        return datetime.now(timezone.utc).isoformat()