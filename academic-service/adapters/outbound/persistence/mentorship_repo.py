from typing import Optional
from uuid import UUID

from application.ports.outbound.mentorship_repository import MentorshipRepositoryPort
from core.models import MentorshipSession as MentorshipSessionORM
from domain.enums import MentorshipSessionStatus
from domain.models import MentorshipSession


class DjangoMentorshipRepository(MentorshipRepositoryPort):

    def save(self, session: MentorshipSession) -> MentorshipSession:
        orm, _ = MentorshipSessionORM.objects.update_or_create(
            id=session.id,
            defaults={
                "teacher_id": session.teacher_id,
                "student_id": session.student_id,
                "scheduled_at": session.scheduled_at,
                "status": session.status.value,
                "notes": session.notes,
            },
        )
        return self._to_domain(orm)

    def find_by_id(self, session_id: UUID) -> Optional[MentorshipSession]:
        try:
            orm = MentorshipSessionORM.objects.get(id=session_id)
        except MentorshipSessionORM.DoesNotExist:
            return None
        return self._to_domain(orm)

    def find_by_student(self, student_id: UUID) -> list[MentorshipSession]:
        queryset = MentorshipSessionORM.objects.filter(student_id=student_id).order_by(
            "-scheduled_at"
        )
        return [self._to_domain(orm) for orm in queryset]

    def find_by_teacher(self, teacher_id: UUID) -> list[MentorshipSession]:
        queryset = MentorshipSessionORM.objects.filter(teacher_id=teacher_id).order_by(
            "-scheduled_at"
        )
        return [self._to_domain(orm) for orm in queryset]

    # ── Mapping ─────────────────────────────────────────────────────────

    def _to_domain(self, orm: MentorshipSessionORM) -> MentorshipSession:
        return MentorshipSession(
            id=orm.id,
            teacher_id=orm.teacher_id,
            student_id=orm.student_id,
            scheduled_at=orm.scheduled_at,
            status=MentorshipSessionStatus(orm.status),
            notes=orm.notes,
            created_at=orm.created_at,
        )