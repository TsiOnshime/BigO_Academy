from typing import Optional
from uuid import UUID

from application.ports.outbound.progress_repository import ProgressRepositoryPort
from core.models import ProblemProgress as ProblemProgressORM
from domain.models import ProblemProgress


class DjangoProgressRepository(ProgressRepositoryPort):

    def save(self, progress: ProblemProgress) -> ProblemProgress:
        # One record per (student, problem) — keyed on that pair rather
        # than id, per the port docstring ("one record per student per
        # problem"). This also makes save() idempotent even if a caller
        # builds a ProblemProgress without reusing the existing id.
        orm, _ = ProblemProgressORM.objects.update_or_create(
            student_id=progress.student_id,
            problem_id=progress.problem_id,
            defaults={
                "id": progress.id,
                "solved": progress.solved,
                "attempt_count": progress.attempt_count,
                "solve_time_minutes": progress.solve_time_minutes,
                "verified_by_teacher": progress.verified_by_teacher,
                "solved_at": progress.solved_at,
            },
        )
        return self._to_domain(orm)

    def find_by_student_and_problem(
        self, student_id: UUID, problem_id: UUID
    ) -> Optional[ProblemProgress]:
        try:
            orm = ProblemProgressORM.objects.get(student_id=student_id, problem_id=problem_id)
        except ProblemProgressORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_all_by_student(
        self, student_id: UUID, topic_id: Optional[UUID] = None
    ) -> list[ProblemProgress]:
        queryset = ProblemProgressORM.objects.filter(student_id=student_id)
        if topic_id is not None:
            queryset = queryset.filter(problem__topic_id=topic_id)
        return [self._to_domain(orm) for orm in queryset]

    def count_solved_by_student(self, student_id: UUID) -> int:
        return ProblemProgressORM.objects.filter(student_id=student_id, solved=True).count()

    # ── Mapping ─────────────────────────────────────────────────────────

    def _to_domain(self, orm: ProblemProgressORM) -> ProblemProgress:
        return ProblemProgress(
            id=orm.id,
            student_id=orm.student_id,
            problem_id=orm.problem_id,
            solved=orm.solved,
            attempt_count=orm.attempt_count,
            solve_time_minutes=orm.solve_time_minutes,
            verified_by_teacher=orm.verified_by_teacher,
            solved_at=orm.solved_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )