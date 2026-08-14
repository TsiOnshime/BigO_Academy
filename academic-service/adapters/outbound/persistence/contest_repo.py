"""
adapters/outbound/persistence/contest_repo.py — Academic Service

Django ORM implementation of ContestRepositoryPort.
"""
from typing import Optional
from uuid import UUID

from django.db import transaction

from application.ports.outbound.contest_repository import ContestRepositoryPort
from core.models import Contest as ContestORM
from core.models import ContestResult as ContestResultORM
from domain.enums import ContestStatus
from domain.models import Contest, ContestResult


class DjangoContestRepository(ContestRepositoryPort):

    def save(self, contest: Contest) -> Contest:
        orm, _ = ContestORM.objects.update_or_create(
            id=contest.id,
            defaults={
                "title": contest.title,
                "cohort_id": contest.cohort_id,
                "external_contest_url": contest.external_contest_url,
                "status": contest.status.value,
                "scheduled_at": contest.scheduled_at,
                "ended_at": contest.ended_at,
                "problem_count": contest.problem_count,
            },
        )
        return self._contest_to_domain(orm)

    def find_by_id(self, contest_id: UUID) -> Optional[Contest]:
        try:
            orm = ContestORM.objects.get(id=contest_id)
        except ContestORM.DoesNotExist:
            return None
        return self._contest_to_domain(orm)

    def find_all_by_cohort(
        self, cohort_id: UUID, status: Optional[ContestStatus] = None
    ) -> list[Contest]:
        queryset = ContestORM.objects.filter(cohort_id=cohort_id)
        if status is not None:
            queryset = queryset.filter(status=status.value)
        return [self._contest_to_domain(orm) for orm in queryset]

    def find_all(self, status: Optional[ContestStatus] = None) -> list[Contest]:
        queryset = ContestORM.objects.all()
        if status is not None:
            queryset = queryset.filter(status=status.value)
        return [self._contest_to_domain(orm) for orm in queryset]

    @transaction.atomic
    def save_results(self, contest_id: UUID, results: list[ContestResult]) -> None:
        ContestResultORM.objects.bulk_create(
            [
                ContestResultORM(
                    contest_id=contest_id,
                    student_id=result.student_id,
                    student_name=result.student_name,
                    contest_rank=result.contest_rank,
                    problems_solved=result.problems_solved,
                    participated=result.participated,
                )
                for result in results
            ]
        )
        ContestORM.objects.filter(id=contest_id).update(status=ContestStatus.FINISHED.value)

    def find_results_by_contest(self, contest_id: UUID) -> list[ContestResult]:
        queryset = ContestResultORM.objects.filter(contest_id=contest_id).order_by("contest_rank")
        return [self._result_to_domain(orm) for orm in queryset]

    def has_results(self, contest_id: UUID) -> bool:
        return ContestResultORM.objects.filter(contest_id=contest_id).exists()

    # ── Mapping ─────────────────────────────────────────────────────────

    def _contest_to_domain(self, orm: ContestORM) -> Contest:
        return Contest(
            id=orm.id,
            title=orm.title,
            cohort_id=orm.cohort_id,
            external_contest_url=orm.external_contest_url,
            status=ContestStatus(orm.status),
            scheduled_at=orm.scheduled_at,
            ended_at=orm.ended_at,
            problem_count=orm.problem_count,
            results=[self._result_to_domain(r) for r in orm.results.all()],
            created_at=orm.created_at,
        )

    def _result_to_domain(self, orm: ContestResultORM) -> ContestResult:
        return ContestResult(
            student_id=orm.student_id,
            student_name=orm.student_name,
            contest_rank=orm.contest_rank,
            problems_solved=orm.problems_solved,
            participated=orm.participated,
        )