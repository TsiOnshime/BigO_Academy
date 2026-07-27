"""
Note on find_escalated: the port signature types cohort_id as a required
UUID, but ListEscalatedWarningsUseCase calls it with
cohort_id=command.cohort_id where command.cohort_id is
Optional[UUID] = None (an admin-wide view across all cohorts when no
cohort is given). This implementation accepts None and treats it as
"no cohort filter", matching the actual call site rather than the
stricter-looking type hint.
"""
from typing import Optional
from uuid import UUID

from application.ports.outbound.warning_repository import WarningRepositoryPort
from core.models import Warning as WarningORM
from domain.enums import WarningStatus, WarningType
from domain.models import Warning


class DjangoWarningRepository(WarningRepositoryPort):

    def save(self, warning: Warning) -> Warning:
        orm, _ = WarningORM.objects.update_or_create(
            id=warning.id,
            defaults={
                "student_id": warning.student_id,
                "type": warning.type.value,
                "status": warning.status.value,
                "warning_number": warning.warning_number,
                "dismissed_at": warning.dismissed_at,
                "dismissed_by": warning.dismissed_by,
                "dismissal_note": warning.dismissal_note,
            },
        )
        return self._to_domain(orm)

    def find_by_id(self, warning_id: UUID) -> Optional[Warning]:
        try:
            orm = WarningORM.objects.get(id=warning_id)
        except WarningORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_by_student(self, student_id: UUID) -> list[Warning]:
        queryset = WarningORM.objects.filter(student_id=student_id).order_by("-issued_at")
        return [self._to_domain(orm) for orm in queryset]

    def count_active_warnings(self, student_id: UUID) -> int:
        return WarningORM.objects.filter(
            student_id=student_id, status=WarningStatus.ACTIVE.value
        ).count()

    def find_escalated(self, cohort_id: Optional[UUID] = None) -> list[Warning]:
        queryset = WarningORM.objects.filter(
            warning_number__gte=3, status=WarningStatus.ESCALATED.value
        )
        if cohort_id is not None:
            queryset = queryset.filter(student__cohort_id=cohort_id)
        return [self._to_domain(orm) for orm in queryset]

    # ── Mapping ─────────────────────────────────────────────────────────

    def _to_domain(self, orm: WarningORM) -> Warning:
        return Warning(
            id=orm.id,
            student_id=orm.student_id,
            type=WarningType(orm.type),
            status=WarningStatus(orm.status),
            warning_number=orm.warning_number,
            issued_at=orm.issued_at,
            dismissed_at=orm.dismissed_at,
            dismissed_by=orm.dismissed_by,
            dismissal_note=orm.dismissal_note,
            # The ORM has no separate created_at column for Warning (only
            # issued_at, auto_now_add) — issued_at is the closest match.
            created_at=orm.issued_at,
        )