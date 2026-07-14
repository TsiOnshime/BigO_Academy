"""
assign_student/unassign_student and assign_teacher/unassign_teacher are the
only places that mutate cohort membership — they keep the denormalized
enrolled_student_count / teacher_count counters in sync in the same
transaction as the membership change.
"""
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.db.models import F

from application.ports.outbound.cohort_repository import CohortRepositoryPort
from core.models import Cohort as CohortORM
from core.models import Student as StudentORM
from core.models import Teacher as TeacherORM
from domain.enums import CohortStatus
from domain.models import Cohort


class DjangoCohortRepository(CohortRepositoryPort):

    def save(self, cohort: Cohort) -> Cohort:
        orm, _ = CohortORM.objects.update_or_create(
            id=cohort.id,
            defaults={
                "name": cohort.name,
                "status": cohort.status.value,
                "intake_window_one": cohort.intake_window_one,
                "intake_window_two": cohort.intake_window_two,
                "start_date": cohort.start_date,
                "expected_graduation_date": cohort.expected_graduation_date,
                "student_capacity": cohort.student_capacity,
                "enrolled_student_count": cohort.enrolled_student_count,
                "teacher_count": cohort.teacher_count,
            },
        )
        return self._to_domain(orm)

    def find_by_id(self, cohort_id: UUID) -> Optional[Cohort]:
        try:
            orm = CohortORM.objects.get(id=cohort_id)
        except CohortORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_all(self, status: Optional[CohortStatus] = None) -> list[Cohort]:
        queryset = CohortORM.objects.all()
        if status is not None:
            queryset = queryset.filter(status=status.value)
        return [self._to_domain(orm) for orm in queryset]

    @transaction.atomic
    def assign_student(self, cohort_id: UUID, student_id: UUID) -> None:
        StudentORM.objects.filter(id=student_id).update(cohort_id=cohort_id)
        CohortORM.objects.filter(id=cohort_id).update(
            enrolled_student_count=F("enrolled_student_count") + 1
        )

    @transaction.atomic
    def unassign_student(self, cohort_id: UUID, student_id: UUID) -> None:
        StudentORM.objects.filter(id=student_id, cohort_id=cohort_id).update(cohort_id=None)
        CohortORM.objects.filter(id=cohort_id).update(
            enrolled_student_count=F("enrolled_student_count") - 1
        )

    @transaction.atomic
    def assign_teacher(self, cohort_id: UUID, teacher_id: UUID) -> None:
        cohort = CohortORM.objects.get(id=cohort_id)
        teacher = TeacherORM.objects.get(id=teacher_id)
        cohort.teachers.add(teacher)
        CohortORM.objects.filter(id=cohort_id).update(
            teacher_count=F("teacher_count") + 1
        )

    @transaction.atomic
    def unassign_teacher(self, cohort_id: UUID, teacher_id: UUID) -> None:
        cohort = CohortORM.objects.get(id=cohort_id)
        teacher = TeacherORM.objects.get(id=teacher_id)
        cohort.teachers.remove(teacher)
        CohortORM.objects.filter(id=cohort_id).update(
            teacher_count=F("teacher_count") - 1
        )

    def student_in_cohort(self, cohort_id: UUID, student_id: UUID) -> bool:
        return StudentORM.objects.filter(id=student_id, cohort_id=cohort_id).exists()

    def teacher_in_cohort(self, cohort_id: UUID, teacher_id: UUID) -> bool:
        return CohortORM.objects.filter(id=cohort_id, teachers__id=teacher_id).exists()

    # ── Mapping ─────────────────────────────────────────────────────────

    def _to_domain(self, orm: CohortORM) -> Cohort:
        return Cohort(
            id=orm.id,
            name=orm.name,
            status=CohortStatus(orm.status),
            intake_window_one=orm.intake_window_one,
            intake_window_two=orm.intake_window_two,
            start_date=orm.start_date,
            expected_graduation_date=orm.expected_graduation_date,
            student_capacity=orm.student_capacity,
            enrolled_student_count=orm.enrolled_student_count,
            teacher_count=orm.teacher_count,
            created_at=orm.created_at,
        )