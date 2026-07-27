from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import ProblemProgress
from domain.exceptions import StudentNotFoundError
from application.ports.outbound.progress_repository import ProgressRepositoryPort
from application.ports.outbound.student_repository import StudentRepositoryPort


@dataclass
class GetStudentProgressCommand:
    student_id: UUID
    topic_id: Optional[UUID] = None


@dataclass
class GetStudentProgressResult:
    student_id: UUID
    total_problems: int
    solved_count: int
    completion_percentage: float
    progress: list[ProblemProgress]


class GetStudentProgressUseCase:

    def __init__(
        self,
        student_repository: StudentRepositoryPort,
        progress_repository: ProgressRepositoryPort,
    ):
        self.student_repository = student_repository
        self.progress_repository = progress_repository

    def execute(self, command: GetStudentProgressCommand) -> GetStudentProgressResult:

        # Student must exist
        student = self.student_repository.find_by_id(command.student_id)
        if student is None:
            raise StudentNotFoundError(str(command.student_id))

        progress = self.progress_repository.find_all_by_student(
            student_id=command.student_id,
            topic_id=command.topic_id,
        )

        total = len(progress)
        solved = sum(1 for p in progress if p.solved)
        percentage = round((solved / total) * 100, 2) if total > 0 else 0.0

        return GetStudentProgressResult(
            student_id=command.student_id,
            total_problems=total,
            solved_count=solved,
            completion_percentage=percentage,
            progress=progress,
        )