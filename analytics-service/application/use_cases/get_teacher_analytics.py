from dataclasses import dataclass
from uuid import UUID

from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.exceptions import TeacherAnalyticsNotFoundError
from domain.enums import RiskReason
from domain.models import StudentAtRisk, TeacherAnalytics, TopPerformer

TOP_PERFORMER_LIMIT = 5


@dataclass
class GetTeacherAnalyticsCommand:
    teacher_id: UUID


class GetTeacherAnalyticsUseCase:
    """
    GET /analytics/teachers/{teacherId}

    NOTE ON AN ASSUMPTION MADE HERE:
    The Analytics Service has no port or table that maps a teacher to
    the cohort(s) they're assigned to -- that mapping lives in the
    Academic Service and isn't published as an event this service
    consumes (see Part 11 of the guide). The only dependency wired in
    for this use case is StudentAnalyticsRepositoryPort, which is
    strictly cohort-scoped (find_all_by_cohort, find_top_performers,
    find_at_risk all take a cohort_id, not a teacher_id).

    To keep this working end-to-end without inventing new
    infrastructure, this implementation treats `teacher_id` as the
    cohort the teacher runs (assigned_cohort_count is therefore always
    1). If a teacher can own multiple cohorts in your real system,
    add a TeacherCohortAssignmentRepositoryPort (populated from an
    Academic Service event, e.g. "academic.teacher.assigned") and loop
    over the returned cohort_ids here instead.
    """

    def __init__(
        self, student_analytics_repository: StudentAnalyticsRepositoryPort
    ):
        self._student_analytics_repository = student_analytics_repository

    def execute(
        self, command: GetTeacherAnalyticsCommand
    ) -> TeacherAnalytics:
        cohort_id = command.teacher_id  # see class docstring

        students = self._student_analytics_repository.find_all_by_cohort(
            cohort_id
        )
        if not students:
            raise TeacherAnalyticsNotFoundError(str(command.teacher_id))

        at_risk_students = self._student_analytics_repository.find_at_risk(
            cohort_id
        )
        top_performers = (
            self._student_analytics_repository.find_top_performers(
                cohort_id, limit=TOP_PERFORMER_LIMIT
            )
        )

        return TeacherAnalytics(
            teacher_id=command.teacher_id,
            assigned_cohort_count=1,
            total_assigned_students=len(students),
            students_at_risk=[
                self._to_student_at_risk(s) for s in at_risk_students
            ],
            top_performers=[
                TopPerformer(
                    student_id=s.student_id,
                    # Student display names aren't part of the
                    # StudentAnalytics domain model (no name-lookup
                    # port exists in this service) -- placeholder
                    # until student profile data is denormalized in.
                    student_name=f"Student {s.student_id}",
                    rank=s.rank,
                    performance_score=s.performance_score,
                    problem_solved_count=s.problem_solved_count,
                )
                for s in top_performers
            ],
            last_updated=max(
                (s.last_updated for s in students),
                default=None,
            ).isoformat()
            if students
            else "",
        )

    def _to_student_at_risk(self, student) -> StudentAtRisk:
        reasons = []
        if student.attendance_percentage < 60.0:
            reasons.append(RiskReason.LOW_ATTENDANCE.value)
        if student.performance_score < 40.0:
            reasons.append(RiskReason.DECLINING_PERFORMANCE.value)
        if student.consistency_score < 40.0:
            reasons.append(RiskReason.DECLINING_CONSISTENCY.value)

        return StudentAtRisk(
            student_id=student.student_id,
            student_name=f"Student {student.student_id}",
            risk_reasons=reasons,
            attendance_percentage=student.attendance_percentage,
            performance_score=student.performance_score,
            active_warning_count=student.active_warning_count,
        )