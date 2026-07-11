from dataclasses import dataclass
from uuid import uuid4, UUID
from typing import Optional
from datetime import datetime, timezone

from domain.models import ProblemProgress
from domain.exceptions import StudentNotFoundError, ProblemNotFoundError
from application.ports.outbound.progress_repository import ProgressRepositoryPort
from application.ports.outbound.student_repository import StudentRepositoryPort
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort


@dataclass
class UpdateProblemProgressCommand:
    student_id: UUID
    problem_id: UUID
    solved: bool
    attempt_count: Optional[int] = None
    solve_time_minutes: Optional[int] = None
    verified_by_teacher: Optional[bool] = None


class UpdateProblemProgressUseCase:

    def __init__(
        self,
        student_repository: StudentRepositoryPort,
        curriculum_repository: CurriculumRepositoryPort,
        progress_repository: ProgressRepositoryPort,
        event_publisher: EventPublisherPort,
    ):
        self.student_repository = student_repository
        self.curriculum_repository = curriculum_repository
        self.progress_repository = progress_repository
        self.event_publisher = event_publisher

    def execute(self, command: UpdateProblemProgressCommand) -> ProblemProgress:

        # Student must exist
        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))

        # Problem must exist
        problem = self.curriculum_repository.find_problem_by_id(command.problem_id)
        if problem is None:
            raise ProblemNotFoundError(str(command.problem_id))

        # Fetch existing progress or create new
        existing = self.progress_repository.find_by_student_and_problem(
            command.student_id,
            command.problem_id,
        )

        # Track if this is a new solve — we only publish event on first solve
        was_already_solved = existing.solved if existing else False

        if existing is not None:
            progress = existing
        else:
            progress = ProblemProgress(
                id=uuid4(),
                student_id=command.student_id,
                problem_id=command.problem_id,
                solved=False,
                attempt_count=0,
                solve_time_minutes=0,
                verified_by_teacher=False,
                solved_at=None,
            )

        # Update fields
        progress.solved = command.solved
        if command.attempt_count is not None:
            progress.attempt_count = command.attempt_count
        if command.solve_time_minutes is not None:
            progress.solve_time_minutes = command.solve_time_minutes
        if command.verified_by_teacher is not None:
            progress.verified_by_teacher = command.verified_by_teacher

        # Set solved_at timestamp only on first solve
        if command.solved and not was_already_solved:
            progress.solved_at = datetime.now(timezone.utc)

        saved_progress = self.progress_repository.save(progress)

        # Publish event only when problem is newly solved — not on re-updates
        if command.solved and not was_already_solved:
            self.event_publisher.publish_problem_solved(
                student_id=command.student_id,
                problem_id=command.problem_id,
                attempts=saved_progress.attempt_count,
                solve_time_minutes=saved_progress.solve_time_minutes,
            )

        return saved_progress