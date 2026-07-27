"""
Django ORM implementation of TeacherRepositoryPort.
"""
from typing import Optional
from uuid import UUID

from application.ports.outbound.teacher_repository import TeacherRepositoryPort
from core.models import Teacher as TeacherORM
from domain.enums import TeacherStatus
from domain.models import Teacher


class DjangoTeacherRepository(TeacherRepositoryPort):

    def save(self, teacher: Teacher) -> Teacher:
        orm, _ = TeacherORM.objects.update_or_create(
            id=teacher.id,
            defaults={
                "user_id": teacher.user_id,
                "full_name": teacher.full_name,
                "email": teacher.email,
                "status": teacher.status.value,
            },
        )
        return self._to_domain(orm)

    def find_by_id(self, teacher_id: UUID) -> Optional[Teacher]:
        try:
            orm = TeacherORM.objects.get(id=teacher_id)
        except TeacherORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_by_user_id(self, user_id: UUID) -> Optional[Teacher]:
        try:
            orm = TeacherORM.objects.get(user_id=user_id)
        except TeacherORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_all(self, status: Optional[TeacherStatus] = None) -> list[Teacher]:
        queryset = TeacherORM.objects.all()
        if status is not None:
            queryset = queryset.filter(status=status.value)
        return [self._to_domain(orm) for orm in queryset]

    def exists_by_user_id(self, user_id: UUID) -> bool:
        return TeacherORM.objects.filter(user_id=user_id).exists()

    # ── Mapping ─────────────────────────────────────────────────────────

    def _to_domain(self, orm: TeacherORM) -> Teacher:
        # assigned_cohort_ids comes from the reverse side of Cohort.teachers
        # (ManyToManyField, related_name="cohorts") — read-only here.
        # Cohort membership itself is mutated only via CohortRepository.
        assigned_cohort_ids = list(orm.cohorts.values_list("id", flat=True))
        return Teacher(
            id=orm.id,
            user_id=orm.user_id,
            full_name=orm.full_name,
            email=orm.email,
            status=TeacherStatus(orm.status),
            assigned_cohort_ids=assigned_cohort_ids,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )