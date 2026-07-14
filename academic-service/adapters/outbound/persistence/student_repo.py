"""
adapters/outbound/persistence/student_repo.py — Academic Service

Django ORM implementation of StudentRepositoryPort.

Never return ORM instances to callers — every method returns domain
dataclasses (or None), converted via _to_domain(). Never accept ORM
instances as input — every method receives a domain Student and converts
it to ORM fields itself.
"""
from typing import Optional
from uuid import UUID

from application.ports.outbound.student_repository import StudentRepositoryPort
from core.models import Student as StudentORM
from domain.enums import StudentStatus, YearPhase
from domain.models import Student


class DjangoStudentRepository(StudentRepositoryPort):

    def save(self, student: Student) -> Student:
        orm, _ = StudentORM.objects.update_or_create(
            id=student.id,
            defaults={
                "user_id": student.user_id,
                "full_name": student.full_name,
                "email": student.email,
                "cohort_id": student.cohort_id,
                "year_phase": student.year_phase.value,
                "status": student.status.value,
                "assigned_teacher_id": student.assigned_teacher_id,
                "attendance_percentage": student.attendance_percentage,
                "active_warning_count": student.active_warning_count,
                "joined_at": student.joined_at,
            },
        )
        return self._to_domain(orm)

    def find_by_id(self, student_id: UUID) -> Optional[Student]:
        try:
            orm = StudentORM.objects.get(id=student_id)
        except StudentORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_by_user_id(self, user_id: UUID) -> Optional[Student]:
        try:
            orm = StudentORM.objects.get(user_id=user_id)
        except StudentORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_all(
        self, cohort_id: Optional[UUID] = None, status: Optional[StudentStatus] = None
    ) -> list[Student]:
        queryset = StudentORM.objects.all()
        if cohort_id is not None:
            queryset = queryset.filter(cohort_id=cohort_id)
        if status is not None:
            queryset = queryset.filter(status=status.value)
        return [self._to_domain(orm) for orm in queryset]

    def exists_by_user_id(self, user_id: UUID) -> bool:
        return StudentORM.objects.filter(user_id=user_id).exists()

    # ── Mapping ─────────────────────────────────────────────────────────

    def _to_domain(self, orm: StudentORM) -> Student:
        return Student(
            id=orm.id,
            user_id=orm.user_id,
            full_name=orm.full_name,
            email=orm.email,
            cohort_id=orm.cohort_id,
            year_phase=YearPhase(orm.year_phase),
            status=StudentStatus(orm.status),
            assigned_teacher_id=orm.assigned_teacher_id,
            attendance_percentage=orm.attendance_percentage,
            active_warning_count=orm.active_warning_count,
            joined_at=orm.joined_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )