from uuid import UUID
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response

from adapters.inbound.rest.auth import JWTAuthMixin
from adapters.inbound.rest.serializers import (
    StudentAnalyticsSerializer,
    StudentAnalyticsSummarySerializer,
    HistoricalMetricSnapshotSerializer,
    LeaderboardEntrySerializer,
    CohortAnalyticsSerializer,
    PlatformAnalyticsSerializer,
)

from domain.exceptions import (
    StudentAnalyticsNotFoundError,
    CohortAnalyticsNotFoundError,
    TeacherAnalyticsNotFoundError,
)


def error_response(status_code, error, message):
    return Response(
        {
            "status": status_code,
            "error": error,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        status=status_code,
    )


# ── Student Analytics Views ─────────────────────────

class StudentAnalyticsView(JWTAuthMixin, APIView):
    """GET /analytics/students/{studentId}"""

    def get(self, request, student_id):
        user = self.require_admin_or_self(request, student_id)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_student_analytics_use_case,
        )

        from application.use_cases.get_student_analytics import (
            GetStudentAnalyticsCommand,
        )

        try:
            use_case = get_student_analytics_use_case()

            result = use_case.execute(
                GetStudentAnalyticsCommand(
                    student_id=UUID(str(student_id))
                )
            )

            return Response(StudentAnalyticsSerializer(result).data)

        except StudentAnalyticsNotFoundError as e:
            return error_response(404, "NOT_FOUND", str(e))


class StudentAnalyticsSummaryView(JWTAuthMixin, APIView):
    """GET /analytics/students/{studentId}/summary"""
    def get(self, request, student_id):
        user = self.require_admin_or_self(request, student_id)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_student_analytics_summary_use_case,
        )
        from application.use_cases.get_student_analytics_summary import (
            GetStudentAnalyticsSummaryCommand,
        )

        try:
            use_case = get_student_analytics_summary_use_case()

            result = use_case.execute(
                GetStudentAnalyticsSummaryCommand(
                    student_id=UUID(str(student_id))
                )
            )

            return Response(StudentAnalyticsSummarySerializer(result).data)

        except StudentAnalyticsNotFoundError as e:
            return error_response(404, "NOT_FOUND", str(e))


class StudentHistoryView(JWTAuthMixin, APIView):
    """GET /analytics/students/{studentId}/history"""

    def get(self, request, student_id):
        user = self.require_admin_or_self(request, student_id)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_student_history_use_case,
        )
        from application.use_cases.get_student_history import (
            GetStudentHistoryCommand,
        )
        from domain.enums import MetricType
        from datetime import date

        metric_param = request.query_params.get("metric")
        from_param = request.query_params.get("from")
        to_param = request.query_params.get("to")

        metric_type = MetricType(metric_param) if metric_param else None
        from_date = date.fromisoformat(from_param) if from_param else None
        to_date = date.fromisoformat(to_param) if to_param else None

        use_case = get_student_history_use_case()

        result = use_case.execute(
            GetStudentHistoryCommand(
                student_id=UUID(str(student_id)),
                metric_type=metric_type,
                from_date=from_date,
                to_date=to_date,
            )
        )

        return Response(
            {
                "studentId": str(student_id),
                "snapshots": HistoricalMetricSnapshotSerializer(
                    result, many=True
                ).data,
            }
        )
        
# ── Leaderboard Views ─────────────────────────────────────────────────────

class GlobalLeaderboardView(JWTAuthMixin, APIView):
    """GET /analytics/leaderboard"""

    def get(self, request):
        user = self.require_auth(request)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_global_leaderboard_use_case,
        )
        from application.use_cases.get_global_leaderboard import (
            GetGlobalLeaderboardCommand,
        )

        page = int(request.query_params.get("page", 0))
        size = int(request.query_params.get("size", 20))

        use_case = get_global_leaderboard_use_case()

        result = use_case.execute(
            GetGlobalLeaderboardCommand(page=page, size=size)
        )

        from adapters.outbound.persistence.leaderboard_repo import (
            DjangoLeaderboardRepository,
        )

        last_refreshed = DjangoLeaderboardRepository().get_last_refreshed()

        return Response(
            {
                "lastRefreshed": last_refreshed,
                "entries": LeaderboardEntrySerializer(result, many=True).data,
            }
        )


class CohortLeaderboardView(JWTAuthMixin, APIView):
    """GET /analytics/leaderboard/cohorts/{cohortId}"""

    def get(self, request, cohort_id):
        user = self.require_auth(request)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_cohort_leaderboard_use_case,
        )
        from application.use_cases.get_cohort_leaderboard import (
            GetCohortLeaderboardCommand,
        )

        page = int(request.query_params.get("page", 0))
        size = int(request.query_params.get("size", 20))

        use_case = get_cohort_leaderboard_use_case()

        result = use_case.execute(
            GetCohortLeaderboardCommand(
                cohort_id=UUID(str(cohort_id)),
                page=page,
                size=size,
            )
        )

        return Response(
            {
                "entries": LeaderboardEntrySerializer(result, many=True).data,
            }
        )


# ── Teacher Analytics Views ───────────────────────────────────────────────

class TeacherAnalyticsView(JWTAuthMixin, APIView):
    """GET /analytics/teachers/{teacherId}"""

    def get(self, request, teacher_id):
        user = self.require_teacher_or_admin(request)

        if isinstance(user, Response):
            return user

        # Teachers can only see their own analytics
        if user.get("role") == "TEACHER":
            if str(user.get("userId")) != str(teacher_id):
                return error_response(
                    403,
                    "FORBIDDEN",
                    "Teachers can only view their own analytics",
                )

        from infrastructure.config.dependencies import (
            get_teacher_analytics_use_case,
        )
        from application.use_cases.get_teacher_analytics import (
            GetTeacherAnalyticsCommand,
        )

        try:
            use_case = get_teacher_analytics_use_case()

            result = use_case.execute(
                GetTeacherAnalyticsCommand(
                    teacher_id=UUID(str(teacher_id))
                )
            )

            return Response(
                {
                    "teacherId": str(result.teacher_id),
                    "assignedCohortCount": result.assigned_cohort_count,
                    "totalAssignedStudents": result.total_assigned_students,
                    "studentsAtRisk": [
                        {
                            "studentId": str(s.student_id),
                            "studentName": s.student_name,
                            "riskReasons": s.risk_reasons,
                            "attendancePercentage": s.attendance_percentage,
                            "performanceScore": s.performance_score,
                            "activeWarningCount": s.active_warning_count,
                        }
                        for s in result.students_at_risk
                    ],
                    "topPerformers": [
                        {
                            "studentId": str(p.student_id),
                            "studentName": p.student_name,
                            "rank": p.rank,
                            "performanceScore": p.performance_score,
                            "problemSolvedCount": p.problem_solved_count,
                        }
                        for p in result.top_performers
                    ],
                    "lastUpdated": result.last_updated,
                }
            )

        except TeacherAnalyticsNotFoundError as e:
            return error_response(404, "NOT_FOUND", str(e))
# ── Admin Analytics Views ─────────────────────────────────────────────────

class PlatformAnalyticsView(JWTAuthMixin, APIView):
    """GET /analytics/admin/platform"""

    def get(self, request):
        user = self.require_admin(request)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_platform_analytics_use_case,
        )

        use_case = get_platform_analytics_use_case()
        result = use_case.execute()

        return Response(PlatformAnalyticsSerializer(result).data)


class AdminCohortAnalyticsView(JWTAuthMixin, APIView):
    """GET /analytics/admin/cohorts/{cohortId}"""

    def get(self, request, cohort_id):
        user = self.require_admin(request)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_cohort_analytics_use_case,
        )
        from application.use_cases.get_cohort_analytics import (
            GetCohortAnalyticsCommand,
        )

        try:
            use_case = get_cohort_analytics_use_case()

            result = use_case.execute(
                GetCohortAnalyticsCommand(
                    cohort_id=UUID(str(cohort_id))
                )
            )

            return Response(CohortAnalyticsSerializer(result).data)

        except CohortAnalyticsNotFoundError as e:
            return error_response(404, "NOT_FOUND", str(e))


class AnalyticsReportView(JWTAuthMixin, APIView):
    """GET /analytics/admin/reports/{reportType}"""

    def get(self, request, report_type):
        user = self.require_admin(request)

        if isinstance(user, Response):
            return user

        from infrastructure.config.dependencies import (
            get_analytics_report_use_case,
        )
        from application.use_cases.get_analytics_report import (
            GetAnalyticsReportCommand,
        )
        from domain.enums import ReportType

        cohort_id = request.query_params.get("cohortId")
        student_id = request.query_params.get("studentId")
        teacher_id = request.query_params.get("teacherId")

        try:
            use_case = get_analytics_report_use_case()

            result = use_case.execute(
                GetAnalyticsReportCommand(
                    report_type=ReportType(report_type.upper()),
                    cohort_id=UUID(cohort_id) if cohort_id else None,
                    student_id=UUID(student_id) if student_id else None,
                    teacher_id=UUID(teacher_id) if teacher_id else None,
                )
            )

            return Response(
                {
                    "reportId": str(result.id),
                    "reportType": result.report_type.value,
                    "generatedAt": result.generated_at.isoformat(),
                    "data": result.data,
                }
            )

        except Exception as e:
            return error_response(400, "BAD_REQUEST", str(e))