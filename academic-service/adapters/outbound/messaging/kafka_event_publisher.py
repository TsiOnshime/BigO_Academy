import json
import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from confluent_kafka import Producer
from django.conf import settings

from application.ports.outbound.event_publisher import EventPublisherPort
from domain.models import Cohort, ContestResult, Student, Teacher, Warning

logger = logging.getLogger(__name__)


def _json_default(value):
    """Serialize the odd types domain dataclasses carry (UUID, date/datetime,
    Enum, Decimal) into plain JSON-friendly values."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "value"):  # Enum members (StudentStatus, YearPhase, ...)
        return value.value
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class KafkaEventPublisher(EventPublisherPort):

    def __init__(self):
        self._producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})

    # ── Student Events ──────────────────────────────────────────────────

    def publish_student_created(self, student: Student) -> None:
        self._publish("academic.student.created", key=str(student.id), payload={
            "student_id": student.id,
            "user_id": student.user_id,
            "full_name": student.full_name,
            "email": student.email,
            "cohort_id": student.cohort_id,
            "status": student.status,
        })

    def publish_student_status_changed(self, student: Student, old_status: str) -> None:
        self._publish("academic.student.status_changed", key=str(student.id), payload={
            "student_id": student.id,
            "old_status": old_status,
            "new_status": student.status,
        })

    def publish_student_promoted(self, student: Student) -> None:
        self._publish("academic.student.promoted", key=str(student.id), payload={
            "student_id": student.id,
            "cohort_id": student.cohort_id,
            "year_phase": student.year_phase,
        })

    def publish_student_graduated(self, student: Student) -> None:
        self._publish("academic.student.graduated", key=str(student.id), payload={
            "student_id": student.id,
            "cohort_id": student.cohort_id,
        })

    def publish_student_dropped(self, student: Student) -> None:
        self._publish("academic.student.dropped", key=str(student.id), payload={
            "student_id": student.id,
            "cohort_id": student.cohort_id,
        })

    # ── Teacher Events ──────────────────────────────────────────────────

    def publish_teacher_created(self, teacher: Teacher) -> None:
        self._publish("academic.teacher.created", key=str(teacher.id), payload={
            "teacher_id": teacher.id,
            "user_id": teacher.user_id,
            "full_name": teacher.full_name,
            "email": teacher.email,
            "status": teacher.status,
        })

    def publish_teacher_status_changed(self, teacher: Teacher) -> None:
        self._publish("academic.teacher.status_changed", key=str(teacher.id), payload={
            "teacher_id": teacher.id,
            "status": teacher.status,
        })

    def publish_teacher_assigned_to_cohort(self, teacher_id: UUID, cohort_id: UUID) -> None:
        self._publish("academic.teacher.assigned_to_cohort", key=str(teacher_id), payload={
            "teacher_id": teacher_id,
            "cohort_id": cohort_id,
        })

    def publish_teacher_unassigned_from_cohort(self, teacher_id: UUID, cohort_id: UUID) -> None:
        self._publish("academic.teacher.unassigned_from_cohort", key=str(teacher_id), payload={
            "teacher_id": teacher_id,
            "cohort_id": cohort_id,
        })

    # ── Cohort Events ───────────────────────────────────────────────────

    def publish_cohort_created(self, cohort: Cohort) -> None:
        self._publish("academic.cohort.created", key=str(cohort.id), payload={
            "cohort_id": cohort.id,
            "name": cohort.name,
            "start_date": cohort.start_date,
            "expected_graduation_date": cohort.expected_graduation_date,
        })

    def publish_cohort_updated(self, cohort: Cohort) -> None:
        self._publish("academic.cohort.updated", key=str(cohort.id), payload={
            "cohort_id": cohort.id,
            "name": cohort.name,
            "status": cohort.status,
        })

    def publish_cohort_archived(self, cohort: Cohort) -> None:
        self._publish("academic.cohort.archived", key=str(cohort.id), payload={
            "cohort_id": cohort.id,
        })

    # ── Academic Activity Events ────────────────────────────────────────

    def publish_problem_solved(
        self, student_id: UUID, problem_id: UUID, attempts: int, solve_time_minutes: int
    ) -> None:
        self._publish("academic.problem.solved", key=str(student_id), payload={
            "student_id": student_id,
            "problem_id": problem_id,
            "attempts": attempts,
            "solve_time_minutes": solve_time_minutes,
        })

    def publish_attendance_updated(self, student_id: UUID, session_id: UUID, status: str) -> None:
        self._publish("academic.attendance.updated", key=str(student_id), payload={
            "student_id": student_id,
            "session_id": session_id,
            "status": status,
        })

    def publish_contest_finished(
        self, contest_id: UUID, cohort_id: UUID, results: list[ContestResult]
    ) -> None:
        self._publish("academic.contest.finished", key=str(contest_id), payload={
            "contest_id": contest_id,
            "cohort_id": cohort_id,
            "results": [
                {
                    "student_id": r.student_id,
                    "student_name": r.student_name,
                    "contest_rank": r.contest_rank,
                    "problems_solved": r.problems_solved,
                    "participated": r.participated,
                }
                for r in results
            ],
        })

    # ── Warning Events ──────────────────────────────────────────────────

    def publish_warning_issued(self, warning: Warning) -> None:
        self._publish("academic.warning.issued", key=str(warning.student_id), payload={
            "warning_id": warning.id,
            "student_id": warning.student_id,
            "type": warning.type,
            "warning_number": warning.warning_number,
        })

    def publish_warning_resolved(self, warning: Warning) -> None:
        self._publish("academic.warning.resolved", key=str(warning.student_id), payload={
            "warning_id": warning.id,
            "student_id": warning.student_id,
        })

    # ── Internals ───────────────────────────────────────────────────────

    def _publish(self, topic: str, key: str, payload: dict) -> None:
        try:
            self._producer.produce(
                topic=topic,
                key=key.encode("utf-8"),
                value=json.dumps(payload, default=_json_default).encode("utf-8"),
                callback=self._delivery_report,
            )
            # Drains any already-completed delivery reports without
            # blocking; does NOT wait for this message's own delivery.
            self._producer.poll(0)
        except BufferError:
            logger.error("Kafka local queue full, dropping event on topic %s", topic)

    @staticmethod
    def _delivery_report(err, msg):
        if err is not None:
            logger.error("Kafka delivery failed for topic %s: %s", msg.topic(), err)

    def flush(self, timeout: float = 10.0) -> None:
        """Block until all buffered messages are delivered or timeout
        elapses. Call this during graceful process shutdown (e.g. from a
        signal handler or management command teardown) — not after every
        publish, which would defeat the point of buffering."""
        self._producer.flush(timeout)
        
class ConsoleEventPublisher(EventPublisherPort):
    """Development/production fallback — logs events instead of sending to Kafka."""

    def _log(self, topic: str, payload: dict) -> None:
        logger.info("EVENT %s: %s", topic, json.dumps(payload, default=_json_default))

    def publish_student_created(self, student): self._log("academic.student.created", {"student_id": str(student.id)})
    def publish_student_status_changed(self, student, old_status): self._log("academic.student.status_changed", {"student_id": str(student.id)})
    def publish_student_promoted(self, student): self._log("academic.student.promoted", {"student_id": str(student.id)})
    def publish_student_graduated(self, student): self._log("academic.student.graduated", {"student_id": str(student.id)})
    def publish_student_dropped(self, student): self._log("academic.student.dropped", {"student_id": str(student.id)})
    def publish_teacher_created(self, teacher): self._log("academic.teacher.created", {"teacher_id": str(teacher.id)})
    def publish_teacher_status_changed(self, teacher): self._log("academic.teacher.status_changed", {"teacher_id": str(teacher.id)})
    def publish_teacher_assigned_to_cohort(self, teacher_id, cohort_id): self._log("academic.teacher.assigned", {})
    def publish_teacher_unassigned_from_cohort(self, teacher_id, cohort_id): self._log("academic.teacher.unassigned", {})
    def publish_cohort_created(self, cohort): self._log("academic.cohort.created", {"cohort_id": str(cohort.id)})
    def publish_cohort_updated(self, cohort): self._log("academic.cohort.updated", {"cohort_id": str(cohort.id)})
    def publish_cohort_archived(self, cohort): self._log("academic.cohort.archived", {"cohort_id": str(cohort.id)})
    def publish_problem_solved(self, student_id, problem_id, attempts, solve_time_minutes): self._log("academic.problem.solved", {})
    def publish_attendance_updated(self, student_id, session_id, status): self._log("academic.attendance.updated", {})
    def publish_contest_finished(self, contest_id, cohort_id, results): self._log("academic.contest.finished", {})
    def publish_warning_issued(self, warning): self._log("academic.warning.issued", {"warning_id": str(warning.id)})
    def publish_warning_resolved(self, warning): self._log("academic.warning.resolved", {"warning_id": str(warning.id)})
    def flush(self, timeout=10.0): pass