"""
Note on find_student_attendance: the port's type hint says
`-> list[ClassSession]`, but the only caller (GetStudentAttendanceUseCase,
in get_student_attendance.py) iterates the result doing `r.status.value`
and `r.note` — fields that live on AttendanceRecord, not ClassSession.
That matches the original PDF guide too ("Filter AttendanceRecord by
student"). This implementation returns list[AttendanceRecord] to match
the real, working contract; flagged to the team as a stale type hint on
the port, not something to "fix" by guessing differently.
"""
from typing import Optional
from uuid import UUID
from datetime import date

from django.db import transaction

from application.ports.outbound.attendance_repository import AttendanceRepositoryPort
from core.models import AttendanceRecord as AttendanceRecordORM
from core.models import ClassSession as ClassSessionORM
from domain.enums import AttendanceStatus
from domain.models import AttendanceRecord, ClassSession


class DjangoAttendanceRepository(AttendanceRepositoryPort):

    @transaction.atomic
    def save_session(self, session: ClassSession) -> ClassSession:
        orm, _ = ClassSessionORM.objects.update_or_create(
            id=session.id,
            defaults={
                "cohort_id": session.cohort_id,
                "session_date": session.session_date,
                "total_students": session.total_students,
                "present_count": session.present_count,
                "absent_count": session.absent_count,
                "excused_count": session.excused_count,
            },
        )

        # domain.AttendanceRecord carries no id/session_id of its own, so
        # the simplest correct sync — used by both first submission and
        # later edits — is: wipe this session's records and recreate them
        # from the domain object's current `records` list.
        AttendanceRecordORM.objects.filter(session=orm).delete()
        AttendanceRecordORM.objects.bulk_create(
            [
                AttendanceRecordORM(
                    session=orm,
                    student_id=record.student_id,
                    status=record.status.value,
                    note=record.note,
                )
                for record in session.records
            ]
        )

        return self._session_to_domain(orm)

    def find_session_by_id(self, session_id: UUID) -> Optional[ClassSession]:
        try:
            orm = ClassSessionORM.objects.prefetch_related("attendance_records").get(
                id=session_id
            )
        except ClassSessionORM.DoesNotExist:
            return None
        return self._session_to_domain(orm)

    def find_sessions_by_cohort(
        self, cohort_id: UUID, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[ClassSession]:
        queryset = ClassSessionORM.objects.prefetch_related("attendance_records").filter(
            cohort_id=cohort_id
        )
        if from_date is not None:
            queryset = queryset.filter(session_date__gte=from_date)
        if to_date is not None:
            queryset = queryset.filter(session_date__lte=to_date)
        return [self._session_to_domain(orm) for orm in queryset]

    def find_student_attendance(
        self, student_id: UUID, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[AttendanceRecord]:
        queryset = AttendanceRecordORM.objects.filter(student_id=student_id)
        if from_date is not None:
            queryset = queryset.filter(session__session_date__gte=from_date)
        if to_date is not None:
            queryset = queryset.filter(session__session_date__lte=to_date)
        queryset = queryset.order_by("session__session_date")
        return [self._record_to_domain(orm) for orm in queryset]

    def calculate_attendance_percentage(self, student_id: UUID) -> float:
        total = AttendanceRecordORM.objects.filter(student_id=student_id).count()
        if total == 0:
            return 100.0
        present = AttendanceRecordORM.objects.filter(
            student_id=student_id, status=AttendanceStatus.PRESENT.value
        ).count()
        percentage = round((present / total) * 100, 2)

        # Keep the denormalized Student.attendance_percentage in sync,
        # per the guide: "Update student.attendance_percentage."
        from core.models import Student as StudentORM

        StudentORM.objects.filter(id=student_id).update(attendance_percentage=percentage)

        return percentage

    # ── Mapping ─────────────────────────────────────────────────────────

    def _session_to_domain(self, orm: ClassSessionORM) -> ClassSession:
        return ClassSession(
            id=orm.id,
            cohort_id=orm.cohort_id,
            session_date=orm.session_date,
            total_students=orm.total_students,
            present_count=orm.present_count,
            absent_count=orm.absent_count,
            excused_count=orm.excused_count,
            records=[self._record_to_domain(r) for r in orm.attendance_records.all()],
            created_at=orm.created_at,
        )

    def _record_to_domain(self, orm: AttendanceRecordORM) -> AttendanceRecord:
        return AttendanceRecord(
            student_id=orm.student_id,
            status=AttendanceStatus(orm.status),
            note=orm.note,
        )