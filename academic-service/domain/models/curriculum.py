from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from domain.enums import (YearPhase, ProblemDifficulty, ProblemSource)

@dataclass
class Topic:
    id: UUID
    curriculum_id: UUID
    title: str
    description: Optional[str]
    year_phase: YearPhase
    display_order: int
    problem_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Problem:
    id: UUID
    topic_id: UUID
    title: str
    source: ProblemSource
    external_url: str
    difficulty: ProblemDifficulty
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
@dataclass
class ProblemProgress:

    id: UUID
    student_id: UUID
    problem_id: UUID
    solved: bool
    attempt_count: int
    solve_time_minutes: int
    verified_by_teacher: bool
    solved_at: Optional[datetime]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))