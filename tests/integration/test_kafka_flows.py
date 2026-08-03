import pytest
import json
import time
from uuid import uuid4
from confluent_kafka import Producer, Consumer


KAFKA_BOOTSTRAP = "localhost:9092"


def publish_event(topic: str, payload: dict):
    """Helper to publish a test event to Kafka."""
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})
    producer.produce(
        topic,
        value=json.dumps(payload, default=str).encode("utf-8"),
    )
    producer.flush()


def wait_for_condition(condition_fn, timeout=10, interval=0.5):
    """Poll until condition is true or timeout."""
    elapsed = 0
    while elapsed < timeout:
        if condition_fn():
            return True
        time.sleep(interval)
        elapsed += interval
    return False


class TestAcademicToAnalyticsKafkaFlow:
    """
    Tests that Academic Service events are correctly
    consumed and processed by Analytics Service.
    """

    def test_problem_solved_event_updates_student_analytics(self):
        """
        When Academic Service publishes academic.problem.solved,
        Analytics Service updates the student's problem_solved_count.
        """
        import django
        import os
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", "config.test_settings"
        )
        django.setup()

        from core.models import StudentAnalyticsModel

        student_id = uuid4()

        # Create initial analytics record
        StudentAnalyticsModel.objects.update_or_create(
            student_id=student_id,
            defaults={
                "problem_solved_count": 0,
                "performance_score": 50.0,
                "consistency_score": 50.0,
            }
        )

        # Publish the event as Academic Service would
        publish_event("academic.problem.solved", {
            "studentId": str(student_id),
            "problemId": str(uuid4()),
            "attempts": 2,
            "solveTime": 25,
            "timestamp": "2025-07-01T10:00:00Z",
        })

        # Wait for Analytics consumer to process it
        def check():
            record = StudentAnalyticsModel.objects.get(
                student_id=student_id
            )
            return record.problem_solved_count > 0

        assert wait_for_condition(check, timeout=10), \
            "Analytics did not process ProblemSolved event within 10 seconds"

    def test_warning_issued_increments_active_warning_count(self):
        """
        When Academic Service publishes academic.warning.issued,
        Analytics Service increments active_warning_count.
        """
        import django
        import os
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", "config.test_settings"
        )
        django.setup()

        from core.models import StudentAnalyticsModel

        student_id = uuid4()

        StudentAnalyticsModel.objects.update_or_create(
            student_id=student_id,
            defaults={"active_warning_count": 0}
        )

        publish_event("academic.warning.issued", {
            "studentId": str(student_id),
            "warningId": str(uuid4()),
            "warningType": "LOW_ATTENDANCE",
            "timestamp": "2025-07-01T10:00:00Z",
        })

        def check():
            record = StudentAnalyticsModel.objects.get(
                student_id=student_id
            )
            return record.active_warning_count > 0

        assert wait_for_condition(check, timeout=10), \
            "Analytics did not process WarningIssued event"