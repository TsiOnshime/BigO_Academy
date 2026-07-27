"""
core/models/__init__.py — Academic Service

Re-exports every model so `core.models` behaves exactly like it did as a
single file (e.g. `from core.models import Student` still works, and
Django's app registry / migration autodetector can see every model here).

Import order follows FK dependency order: a model must be imported only
after everything it points to.
"""
from core.models.teacher import Teacher
from core.models.cohort import Cohort
from core.models.student import Student
from core.models.curriculum import Topic, Problem
from core.models.progress import ProblemProgress
from core.models.attendance import ClassSession, AttendanceRecord
from core.models.contest import Contest, ContestResult
from core.models.warning import Warning
from core.models.mentorship import MentorshipSession
from core.models.warning_rules import WarningRulesConfig

__all__ = [
    "Teacher",
    "Cohort",
    "Student",
    "Topic",
    "Problem",
    "ProblemProgress",
    "ClassSession",
    "AttendanceRecord",
    "Contest",
    "ContestResult",
    "Warning",
    "MentorshipSession",
    "WarningRulesConfig",
]