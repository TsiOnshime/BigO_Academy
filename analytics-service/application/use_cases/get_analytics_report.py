from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from application.ports.outbound.analytics_report_repository import (
    AnalyticsReportRepositoryPort,
)
from application.ports.outbound.cohort_analytics_repository import (
    CohortAnalyticsRepositoryPort,
)
from application.ports.outbound.student_analytics_repository import (
    StudentAnalyticsRepositoryPort,
)
from domain.enums import ReportType
from domain.exceptions import (
    CohortAnalyticsNotFoundError,
    StudentAnalyticsNotFoundError,
    TeacherAnalyticsNotFoundError,
)
from domain.models import AnalyticsReport

TOP_PERFORMER_LIMIT = 5


@dataclass
class GetAnalyticsReportCommand:
    report_type: ReportType
    cohort_id: Optional[UUID] = None
    student_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None


class GetAnalyticsReportUseCase:
    """
    GET /analytics/admin/reports/{reportType}

    Builds a report snapshot for the requested scope, persists it
    (AnalyticsReportModel is an append-only log of generated reports),
    and returns the saved record.
    """

    def __init__(
        self,
        student_analytics_repository: StudentAnalyticsRepositoryPort,
        cohort_analytics_repository: CohortAnalyticsRepositoryPort,
        analytics_report_repository: AnalyticsReportRepositoryPort,
    ):
        self._student_analytics_repository = student_analytics_repository
        self._cohort_analytics_repository = cohort_analytics_repository
        self._analytics_report_repository = analytics_report_repository

    def execute(
        self, command: GetAnalyticsReportCommand
    ) -> AnalyticsReport:
        builders = {
            ReportType.STUDENT: self._build_student_report,
            ReportType.TEACHER: self._build_teacher_report,
            ReportType.COHORT: self._build_cohort_report,
            ReportType.PLATFORM: self._build_platform_report,
        }
        builder = builders[command.report_type]
        data = builder(command)

        report = AnalyticsReport(
            id=uuid4(),
            report_type=command.report_type,
            data=data,
        )
        return self._analytics_report_repository.save(report)

    def _build_student_report(self, command: GetAnalyticsReportCommand) -> dict:
        if command.student_id is None:
            raise ValueError("studentId is required for a STUDENT report")

        analytics = self._student_analytics_repository.find_by_student_id(
            command.student_id
        )
        if analytics is None:
            raise StudentAnalyticsNotFoundError(str(command.student_id))

        return {
            "studentId": str(analytics.student_id),
            "rank": analytics.rank,
            "rating": analytics.rating,
            "performanceScore": analytics.performance_score,
            "consistencyScore": analytics.consistency_score,
            "attendancePercentage": analytics.attendance_percentage,
            "problemSolvedCount": analytics.problem_solved_count,
            "currentStreak": analytics.current_streak,
            "longestStreak": analytics.longest_streak,
            "activeWarningCount": analytics.active_warning_count,
        }

    def _build_teacher_report(self, command: GetAnalyticsReportCommand) -> dict:
        # See GetTeacherAnalyticsUseCase docstring: this service has no
        # teacher-to-cohort mapping, so teacher_id is treated as the
        # cohort the teacher runs.
        if command.teacher_id is None:
            raise ValueError("teacherId is required for a TEACHER report")

        cohort_id = command.teacher_id
        students = self._student_analytics_repository.find_all_by_cohort(
            cohort_id
        )
        if not students:
            raise TeacherAnalyticsNotFoundError(str(command.teacher_id))

        at_risk = self._student_analytics_repository.find_at_risk(cohort_id)
        top_performers = (
            self._student_analytics_repository.find_top_performers(
                cohort_id, limit=TOP_PERFORMER_LIMIT
            )
        )

        return {
            "teacherId": str(command.teacher_id),
            "totalAssignedStudents": len(students),
            "atRiskCount": len(at_risk),
            "topPerformerStudentIds": [
                str(s.student_id) for s in top_performers
            ],
        }

    def _build_cohort_report(self, command: GetAnalyticsReportCommand) -> dict:
        if command.cohort_id is None:
            raise ValueError("cohortId is required for a COHORT report")

        cohort = self._cohort_analytics_repository.find_by_cohort_id(
            command.cohort_id
        )
        if cohort is None:
            raise CohortAnalyticsNotFoundError(str(command.cohort_id))

        return {
            "cohortId": str(cohort.cohort_id),
            "cohortName": cohort.cohort_name,
            "totalStudents": cohort.total_students,
            "averagePerformanceScore": cohort.average_performance_score,
            "averageAttendancePercentage": cohort.average_attendance_percentage,
            "averageConsistencyScore": cohort.average_consistency_score,
            "activeWarnings": cohort.warning_stats.active_warnings,
            "studentsOnProbation": cohort.warning_stats.students_on_probation,
            "graduated": cohort.progression_stats.graduated,
            "dropped": cohort.progression_stats.dropped,
        }

    def _build_platform_report(
        self, command: GetAnalyticsReportCommand
    ) -> dict:
        cohorts = self._cohort_analytics_repository.find_all()
        total_students = sum(c.total_students for c in cohorts)

        return {
            "totalCohorts": len(cohorts),
            "totalStudents": total_students,
            "totalWarningsIssued": sum(
                c.warning_stats.total_issued for c in cohorts
            ),
            "totalGraduates": sum(
                c.progression_stats.graduated for c in cohorts
            ),
            "totalDropped": sum(
                c.progression_stats.dropped for c in cohorts
            ),
        }