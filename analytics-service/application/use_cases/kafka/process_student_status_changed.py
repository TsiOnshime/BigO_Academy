from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from application.ports.outbound.cohort_analytics_repository import (
    CohortAnalyticsRepositoryPort,
)
from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.exceptions import StudentAnalyticsNotFoundError
from domain.models import CohortAnalytics, ProgressionStats


@dataclass
class ProcessStudentStatusChangedCommand:
    student_id: UUID
    new_status: str
    timestamp: Optional[str] = None


class ProcessStudentStatusChangedUseCase:
    """
    Kafka consumer target for: academic.student.status

    NOTE: `status` (e.g. GRADUATED / DROPPED / ACTIVE / PROBATION)
    isn't tracked per-student in the current domain model, so the
    cohort's progression_stats counters are incremented for the new
    status without being able to decrement whatever bucket the student
    was previously counted under (that would require storing the
    student's prior status somewhere, which this service doesn't do
    today). Good enough for "how many students have ever graduated /
    dropped," not for a live headcount by status.
    """

    def __init__(
        self,
        student_analytics_repository: StudentAnalyticsRepositoryPort,
        cohort_analytics_repository: CohortAnalyticsRepositoryPort,
    ):
        self._student_analytics_repository = student_analytics_repository
        self._cohort_analytics_repository = cohort_analytics_repository

    def execute(self, command: ProcessStudentStatusChangedCommand) -> None:
        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            raise StudentAnalyticsNotFoundError(str(command.student_id))

        if analytics.cohort_id is None:
            return

        cohort = self._cohort_analytics_repository.find_by_cohort_id(
            analytics.cohort_id
        )
        if cohort is None:
            return

        progression = cohort.progression_stats
        status = command.new_status.upper()

        if status == "GRADUATED":
            progression = ProgressionStats(
                promoted_to_year2=progression.promoted_to_year2,
                graduated=progression.graduated + 1,
                dropped=progression.dropped,
                active=progression.active,
            )
        elif status == "DROPPED":
            progression = ProgressionStats(
                promoted_to_year2=progression.promoted_to_year2,
                graduated=progression.graduated,
                dropped=progression.dropped + 1,
                active=progression.active,
            )
        elif status in ("ACTIVE", "PROMOTED"):
            progression = ProgressionStats(
                promoted_to_year2=progression.promoted_to_year2 + 1
                if status == "PROMOTED"
                else progression.promoted_to_year2,
                graduated=progression.graduated,
                dropped=progression.dropped,
                active=progression.active + 1,
            )

        updated = CohortAnalytics(
            cohort_id=cohort.cohort_id,
            cohort_name=cohort.cohort_name,
            total_students=cohort.total_students,
            average_performance_score=cohort.average_performance_score,
            average_attendance_percentage=cohort.average_attendance_percentage,
            average_consistency_score=cohort.average_consistency_score,
            warning_stats=cohort.warning_stats,
            progression_stats=progression,
            last_updated="",  # ORM sets this via auto_now on save
        )
        self._cohort_analytics_repository.save(updated)