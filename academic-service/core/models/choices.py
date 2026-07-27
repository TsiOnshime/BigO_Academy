"""
core/models/choices.py — Academic Service

Django choices mirrored from domain/enums.py, shared across the model
package. Values must stay byte-for-byte identical to the domain enums so
that ORM <-> domain mapping in the repository adapters is a plain pass-through.
"""
from django.db import models


class StudentStatusChoices(models.TextChoices):
    ACTIVE = "ACTIVE"
    PROBATION = "PROBATION"
    DROPPED = "DROPPED"
    GRADUATED = "GRADUATED"
    ARCHIVED = "ARCHIVED"


class TeacherStatusChoices(models.TextChoices):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CohortStatusChoices(models.TextChoices):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class AttendanceStatusChoices(models.TextChoices):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    EXCUSED = "EXCUSED"


class ContestStatusChoices(models.TextChoices):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


class WarningStatusChoices(models.TextChoices):
    ACTIVE = "ACTIVE"
    DISMISSED = "DISMISSED"
    ESCALATED = "ESCALATED"


class WarningTypeChoices(models.TextChoices):
    LOW_ATTENDANCE = "LOW_ATTENDANCE"
    LOW_PERFORMANCE = "LOW_PERFORMANCE"
    LOW_CONSISTENCY = "LOW_CONSISTENCY"
    WEAK_CONTEST_PARTICIPATION = "WEAK_CONTEST_PARTICIPATION"


class ProblemSourceChoices(models.TextChoices):
    LEETCODE = "LEETCODE"
    CODEFORCES = "CODEFORCES"


class ProblemDifficultyChoices(models.TextChoices):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class MentorshipSessionStatusChoices(models.TextChoices):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# YearPhase is an int enum (1, 2) in the domain layer — kept as a plain
# IntegerField choices tuple rather than TextChoices.
YEAR_PHASE_CHOICES = [
    (1, "Year 1"),
    (2, "Year 2"),
]