import json 
import logging
from confluent_kafka import Consumer, KafkaError
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseConsumer:
    def __init__(self, topic: str):
        self.topic = topic
        self.consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": settings.KAFKA_CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True
        })
        self.consumer.subscribe([topic])
        
    def handle(self, payload: dict) -> None:
        '''Override in subclass to process each message.'''
        raise NotImplementedError
    
    def run(self) -> None:
        '''Start consuming messages. Blocks indefinitely'''
        logger.info(f"Starting consumer for topic: {self.topic}")
        try: 
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka error: {msg.error()}")
                try:
                    payload = json.loads(msg.value().decode("utf-8"))
                    self.handle(payload)
                except Exception as e:
                    logger.error(
                        f"Error processing message from {self.topic}: {e}"
                    )
        finally:
            self.consumer.close()
    
    class ProblemSolvedConsumer(BaseConsumer):
        """
        Listens to: academic.problem.solved
        Payload: studentId, problemId, attempts, solveTime Updates: problem_solved_count, consistency_score, """
        def __init__(self):
            super().__init__("academic.problem.solved")
        def handle(self, payload: dict) -> None:
            from infrastructure.config.dependencies import (
                get_process_problem_solved_use_case
            )
            from application.use_cases.process_problem_solved import (ProcessProblemSolvedCommand)
            from uuid import UUID
            
            use_case = get_process_problem_solved_use_case()
  
            use_case = get_process_problem_solved_use_case()

            use_case.execute(
                ProcessProblemSolvedCommand(
                    student_id=UUID(payload["studentId"]),
                    problem_id=UUID(payload["problemId"]),
                    attempts=payload.get("attempts", 1),
                    solve_time_minutes=payload.get("solveTime", 0),
                    timestamp=payload.get("timestamp"),
        ))

class AttendanceUpdatedConsumer(BaseConsumer):
    """
    Listens to: academic.attendance.updated
    Payload: studentId, sessionId, status, timestamp
    Updates: attendance_percentage, performance_score
    """

    def __init__(self):
        super().__init__("academic.attendance.updated")

    def handle(self, payload: dict) -> None:
        from infrastructure.config.dependencies import (
            get_process_attendance_updated_use_case,
        )
        from application.use_cases.process_attendance_updated import (
            ProcessAttendanceUpdatedCommand,
        )
        from uuid import UUID

        use_case = get_process_attendance_updated_use_case()

        use_case.execute(
            ProcessAttendanceUpdatedCommand(
                student_id=UUID(payload["studentId"]),
                session_id=UUID(payload["sessionId"]),
                status=payload["status"],
                timestamp=payload.get("timestamp"),
            )
        )

        logger.info(
            f"Processed AttendanceUpdated for student {payload['studentId']}"
        )


class ContestFinishedConsumer(BaseConsumer):
    """
    Listens to: academic.contest.finished
    Payload: contestId, cohortId, results[], timestamp
    Updates: contest_stats, rating, ranking
    """

    def __init__(self):
        super().__init__("academic.contest.finished")

    def handle(self, payload: dict) -> None:
        from infrastructure.config.dependencies import (
            get_process_contest_finished_use_case,
        )
        from application.use_cases.process_contest_finished import (
            ProcessContestFinishedCommand,
        )
        from uuid import UUID

        use_case = get_process_contest_finished_use_case()

        use_case.execute(
            ProcessContestFinishedCommand(
                contest_id=UUID(payload["contestId"]),
                cohort_id=UUID(payload["cohortId"]),
                results=payload.get("results", []),
                timestamp=payload.get("timestamp"),
            )
        )

        logger.info(
            f"Processed ContestFinished: {payload['contestId']}"
        )


class WarningIssuedConsumer(BaseConsumer):
    """
    Listens to: academic.warning.issued
    Payload: studentId, warningId, warningType, timestamp
    Updates: active_warning_count
    """

    def __init__(self):
        super().__init__("academic.warning.issued")

    def handle(self, payload: dict) -> None:
        from infrastructure.config.dependencies import ( get_process_warning_issued_use_case,
        )
        from application.use_cases.process_warning_issued import (
            ProcessWarningIssuedCommand,
        )
        from uuid import UUID

        use_case = get_process_warning_issued_use_case()

        use_case.execute(
            ProcessWarningIssuedCommand(
                student_id=UUID(payload["studentId"]),
                warning_id=UUID(payload["warningId"]),
                warning_type=payload["warningType"],
                timestamp=payload.get("timestamp"),
            )
        )


class WarningResolvedConsumer(BaseConsumer):
    """
    Listens to: academic.warning.resolved
    Payload: studentId, warningId, timestamp
    Updates: active_warning_count
    """

    def __init__(self):
        super().__init__("academic.warning.resolved")

    def handle(self, payload: dict) -> None:
        from infrastructure.config.dependencies import (
            get_process_warning_resolved_use_case,
        )
        from application.use_cases.process_warning_resolved import (
            ProcessWarningResolvedCommand,
        )
        from uuid import UUID

        use_case = get_process_warning_resolved_use_case()

        use_case.execute(
            ProcessWarningResolvedCommand(
                student_id=UUID(payload["studentId"]),
                warning_id=UUID(payload["warningId"]),
                timestamp=payload.get("timestamp"),
            )
        )


class StudentPromotedConsumer(BaseConsumer):
    """
    Listens to: academic.student.promoted

    Payload: studentId, timestamp
    """

    def __init__(self):
        super().__init__("academic.student.promoted")

    def handle(self, payload: dict) -> None:
        from infrastructure.config.dependencies import (
            get_process_student_promoted_use_case,
        )
        from application.use_cases.process_student_promoted import (
            ProcessStudentPromotedCommand,
        )
        from uuid import UUID

        use_case = get_process_student_promoted_use_case()

        use_case.execute(
            ProcessStudentPromotedCommand(
                student_id=UUID(payload["studentId"]),
                timestamp=payload.get("timestamp"),
            )
        )


class StudentStatusChangedConsumer(BaseConsumer):
    """
    Listens to: academic.student.status

    Payload: studentId, newStatus, oldStatus, timestamp
    """

    def __init__(self):
        super().__init__("academic.student.status")

    def handle(self, payload: dict) -> None:
        from infrastructure.config.dependencies import (
            get_process_student_status_changed_use_case,
        )
        from application.use_cases.process_student_status_changed import (
            ProcessStudentStatusChangedCommand,
        )
        from uuid import UUID

        use_case = get_process_student_status_changed_use_case()

        use_case.execute(
            ProcessStudentStatusChangedCommand(
                student_id=UUID(payload["studentId"]),
                new_status=payload["newStatus"],
                timestamp=payload.get("timestamp"),
            )
        )