"""
adapters/outbound/messaging/kafka_event_publisher.py — Academic Service

Django/confluent-kafka implementation of EventPublisherPort.

Note: this file implements the port as it actually is (17 methods, see
application/ports/outbound/event_publisher.py) rather than the 14-event
list in the original PDF guide — the two differ in method names,
argument shapes, and a couple of events entirely (e.g. the port has no
publish_student_dropped(student_id, cohort_id)-style signature; it takes
a full Student). Always trust the port file over the guide.

Topic naming: 'academic.<entity>.<event>', mirroring the
'auth.<entity>.<event>' convention the guide uses for the consumer side
(see infrastructure/kafka/consumers.py).

Delivery: fire-and-forget with an async delivery callback that only logs.
A single shared Producer per process; produce() buffers locally and
poll(0) drains the delivery-report queue without blocking the caller.
flush() is not called per-publish — that would turn every event publish
into a network round trip. main.py / the process exit path should call
producer.flush() during graceful shutdown so nothing is lost in the
local buffer; a management-command-friendly helper for that is exposed
as KafkaEventPublisher.flush().
"""
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