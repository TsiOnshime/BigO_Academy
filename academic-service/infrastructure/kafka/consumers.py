"""
infrastructure/kafka/consumers.py — Academic Service

Consumer side of the event-driven layer. adapters/outbound/messaging/
kafka_event_publisher.py already implements the PRODUCER side (Academic
Service publishing academic.* events for Analytics Service to consume).
This file is the other direction: Academic Service consuming events
published BY Auth Service, so profile creation/deactivation can react to
account lifecycle changes instead of requiring a second manual step.

IMPORTANT — anticipated contract, not a confirmed one: auth-service (as
shipped in this repo) has no Kafka producer at all — its adapters/
outbound/messaging/ only has email_adapter.py. So the two topics this
consumer subscribes to, `auth.user.registered` and
`auth.account.deactivated`, do not yet exist anywhere. They're modeled
here on the same 'service.entity.event' naming convention
kafka_event_publisher.py already uses for the academic.* topics, and on
the User fields visible in auth-service/domain/models.py (id, email,
full_name, role, status). Confirm the exact topic names/payload shape
with whoever builds auth-service's producer before running this in a
real environment — treat every field access below as provisional.

Why these two topics and not others: 
  - CreateTeacherCommand only needs user_id/full_name/email — no cohort
    dependency — so a Teacher profile CAN be safely auto-provisioned the
    moment an Auth Service account with role=TEACHER is registered.
  - CreateStudentCommand additionally requires cohort_id, which
    registration never provides (see auth-service's
    RegisterStudentCommand — no cohort field). Auto-creating a Student
    profile here isn't possible without inventing a default cohort
    assignment, which is an admin decision, not this consumer's to make.
    So role=STUDENT registrations are logged and skipped, not force-fit
    into CreateStudentUseCase.
  - Deactivation is symmetric for both roles: TeacherRepositoryPort and
    StudentRepositoryPort both expose find_by_user_id(...), so either
    profile can be looked up and status-synced without any new port
    method.

Idempotency: at-least-once delivery is assumed (manual offset commit
after successful processing, see AcademicKafkaConsumer.run() below).
Handlers below tolerate re-delivery: TeacherAlreadyExistsError from a
duplicate `auth.user.registered` is caught and logged as a no-op rather
than crashing the consumer loop.
"""
import json
import logging
import signal
from uuid import UUID

from confluent_kafka import Consumer, KafkaError
from django.conf import settings

from application.use_cases.student.update_student_status import (
    UpdateStudentStatusCommand,
)
from application.use_cases.teacher.create_teacher import CreateTeacherCommand
from application.use_cases.teacher.deactivate_teacher import DeactivateTeacherCommand
from domain.enums import StudentStatus
from domain.exceptions import (
    StudentNotFoundError,
    TeacherAlreadyExistsError,
    TeacherNotFoundError,
)
from infrastructure.config.dependencies import (
    get_create_teacher_use_case,
    get_deactivate_teacher_use_case,
    get_student_repository,
    get_teacher_repository,
    get_update_student_status_use_case,
)

logger = logging.getLogger(__name__)

# Anticipated topics published by Auth Service — see module docstring.
TOPIC_USER_REGISTERED = "auth.user.registered"
TOPIC_ACCOUNT_DEACTIVATED = "auth.account.deactivated"

CONSUMER_GROUP_ID = "academic-service"


def handle_user_registered(payload: dict) -> None:
    """
    Expected payload (provisional — see module docstring):
        {"user_id": "<uuid>", "full_name": "...", "email": "...",
         "role": "STUDENT" | "TEACHER" | "ADMIN"}
    """
    role = payload.get("role")
    user_id = payload.get("user_id")
    if not user_id or not role:
        logger.warning("auth.user.registered: missing user_id/role, skipping: %s", payload)
        return

    if role == "TEACHER":
        try:
            use_case = get_create_teacher_use_case()
            use_case.execute(
                CreateTeacherCommand(
                    user_id=UUID(user_id),
                    full_name=payload.get("full_name", ""),
                    email=payload.get("email", ""),
                )
            )
            logger.info("Auto-provisioned Teacher profile for user_id=%s", user_id)
        except TeacherAlreadyExistsError:
            # Re-delivery of the same event — already handled, no-op.
            logger.info(
                "Teacher profile already exists for user_id=%s, skipping", user_id
            )
    elif role == "STUDENT":
        # See module docstring: CreateStudentCommand requires cohort_id,
        # which registration never supplies. Cohort assignment is an
        # admin action via POST /students/, not something this consumer
        # can infer. Logged so the gap is visible, not silently dropped.
        logger.info(
            "Student user_id=%s registered in Auth Service; skipping "
            "auto-provisioning — cohort assignment must be done via "
            "POST /students/ (CreateStudentCommand requires cohort_id, "
            "which registration doesn't provide).",
            user_id,
        )
    else:
        logger.debug("auth.user.registered: role=%s ignored (user_id=%s)", role, user_id)


def handle_account_deactivated(payload: dict) -> None:
    """
    Expected payload (provisional — see module docstring):
        {"user_id": "<uuid>", "role": "STUDENT" | "TEACHER" | "ADMIN"}
    """
    role = payload.get("role")
    user_id_raw = payload.get("user_id")
    if not user_id_raw or not role:
        logger.warning(
            "auth.account.deactivated: missing user_id/role, skipping: %s", payload
        )
        return
    user_id = UUID(user_id_raw)

    if role == "TEACHER":
        teacher = get_teacher_repository().find_by_user_id(user_id)
        if teacher is None:
            logger.info(
                "No Teacher profile for deactivated user_id=%s, skipping", user_id
            )
            return
        try:
            get_deactivate_teacher_use_case().execute(
                DeactivateTeacherCommand(teacher_id=teacher.id)
            )
            logger.info("Deactivated Teacher profile for user_id=%s", user_id)
        except TeacherNotFoundError:
            logger.info("Teacher for user_id=%s vanished mid-processing, skipping", user_id)

    elif role == "STUDENT":
        student = get_student_repository().find_by_user_id(user_id)
        if student is None:
            logger.info(
                "No Student profile for deactivated user_id=%s, skipping", user_id
            )
            return
        try:
            # ARCHIVED is reachable from every status (see
            # domain.models.Student.can_transition_to), so this is the
            # one status-sync target that's always valid regardless of
            # the student's current lifecycle stage.
            get_update_student_status_use_case().execute(
                UpdateStudentStatusCommand(
                    student_id=student.id,
                    new_status=StudentStatus.ARCHIVED,
                    reason="Auth Service account deactivated",
                )
            )
            logger.info("Archived Student profile for user_id=%s", user_id)
        except StudentNotFoundError:
            logger.info("Student for user_id=%s vanished mid-processing, skipping", user_id)
    else:
        logger.debug(
            "auth.account.deactivated: role=%s ignored (user_id=%s)", role, user_id
        )


_HANDLERS = {
    TOPIC_USER_REGISTERED: handle_user_registered,
    TOPIC_ACCOUNT_DEACTIVATED: handle_account_deactivated,
}


class AcademicKafkaConsumer:
    """
    Wraps a confluent_kafka.Consumer subscribed to every topic in
    _HANDLERS, dispatching each message to its handler and committing
    the offset only after the handler returns successfully (at-least-
    once delivery — a crash mid-handler means that message is
    redelivered on restart, which the handlers above are written to
    tolerate).
    """

    def __init__(self):
        self._consumer = Consumer(
            {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "group.id": CONSUMER_GROUP_ID,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self._running = False

    def run(self) -> None:
        self._consumer.subscribe(list(_HANDLERS.keys()))
        self._running = True

        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        logger.info(
            "AcademicKafkaConsumer started, subscribed to: %s",
            list(_HANDLERS.keys()),
        )
        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("Kafka consumer error: %s", msg.error())
                    continue

                self._process_message(msg)
        finally:
            self._consumer.close()
            logger.info("AcademicKafkaConsumer stopped.")

    def _process_message(self, msg) -> None:
        topic = msg.topic()
        handler = _HANDLERS.get(topic)
        if handler is None:
            logger.warning("No handler registered for topic %s, skipping", topic)
            self._consumer.commit(msg)
            return

        try:
            payload = json.loads(msg.value().decode("utf-8"))
            handler(payload)
        except Exception:
            # Do NOT commit on failure — leaving the offset uncommitted
            # means this message is redelivered on the next poll/restart
            # rather than silently lost.
            logger.exception(
                "Failed to process message on topic %s (offset %s); will retry",
                topic,
                msg.offset(),
            )
            return

        self._consumer.commit(msg)

    def _handle_shutdown(self, signum, frame) -> None:
        logger.info("Shutdown signal received, stopping consumer loop...")
        self._running = False