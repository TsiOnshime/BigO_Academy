from adapters.outbound.persistence.student_analytics_repo import (
    DjangoStudentAnalyticsRepository,
)
from adapters.outbound.persistence.leaderboard_repo import (
    DjangoLeaderboardRepository,
)
from adapters.outbound.persistence.historical_metrics_repo import (
    DjangoHistoricalMetricsRepository,
)
from adapters.outbound.persistence.cohort_analytics_repo import (
    DjangoCohortAnalyticsRepository,
)
from adapters.outbound.persistence.analytics_report_repo import (
    DjangoAnalyticsReportRepository,
)


def get_student_analytics_repo():
    return DjangoStudentAnalyticsRepository()


def get_leaderboard_repo():
    return DjangoLeaderboardRepository()


def get_historical_metrics_repo():
    return DjangoHistoricalMetricsRepository()


def get_cohort_analytics_repo():
    return DjangoCohortAnalyticsRepository()


def get_analytics_report_repo():
    return DjangoAnalyticsReportRepository()


# ── Read Use Cases ──────────────────────────────────

def get_student_analytics_use_case():
    from application.use_cases.get_student_analytics import (
        GetStudentAnalyticsUseCase,
    )

    return GetStudentAnalyticsUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_student_analytics_summary_use_case():
    from application.use_cases.get_student_analytics_summary import (
        GetStudentAnalyticsSummaryUseCase,
    )

    return GetStudentAnalyticsSummaryUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_student_history_use_case():
    from application.use_cases.get_student_history import (
        GetStudentHistoryUseCase,
    )

    return GetStudentHistoryUseCase(
        historical_metrics_repository=get_historical_metrics_repo(),
    )


def get_global_leaderboard_use_case():
    from application.use_cases.get_global_leaderboard import (
        GetGlobalLeaderboardUseCase,
    )

    return GetGlobalLeaderboardUseCase(
        leaderboard_repository=get_leaderboard_repo(),
    )


def get_cohort_leaderboard_use_case():
    from application.use_cases.get_cohort_leaderboard import (
        GetCohortLeaderboardUseCase,
    )

    return GetCohortLeaderboardUseCase(
        leaderboard_repository=get_leaderboard_repo(),
    )


def get_teacher_analytics_use_case():
    from application.use_cases.get_teacher_analytics import (
        GetTeacherAnalyticsUseCase,
    )

    return GetTeacherAnalyticsUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_platform_analytics_use_case():
    from application.use_cases.get_platform_analytics import (
        GetPlatformAnalyticsUseCase,
    )

    return GetPlatformAnalyticsUseCase(
        student_analytics_repository=get_student_analytics_repo(),
        cohort_analytics_repository=get_cohort_analytics_repo(),
    )


def get_cohort_analytics_use_case():
    from application.use_cases.get_cohort_analytics import (
        GetCohortAnalyticsUseCase,
    )

    return GetCohortAnalyticsUseCase(
        cohort_analytics_repository=get_cohort_analytics_repo(),
    )
def get_analytics_report_use_case():
    from application.use_cases.get_analytics_report import (
        GetAnalyticsReportUseCase,
    )

    return GetAnalyticsReportUseCase(
        student_analytics_repository=get_student_analytics_repo(),
        cohort_analytics_repository=get_cohort_analytics_repo(),
        analytics_report_repository=get_analytics_report_repo(),
    )


# ── Event Processing Use Cases ──────────────────────

def get_process_problem_solved_use_case():
    from application.use_cases.process_problem_solved import (
        ProcessProblemSolvedUseCase,
    )

    return ProcessProblemSolvedUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_process_attendance_updated_use_case():
    from application.use_cases.process_attendance_updated import (
        ProcessAttendanceUpdatedUseCase,
    )

    return ProcessAttendanceUpdatedUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_process_contest_finished_use_case():
    from application.use_cases.process_contest_finished import (
        ProcessContestFinishedUseCase,
    )

    return ProcessContestFinishedUseCase(
        student_analytics_repository=get_student_analytics_repo(),
        cohort_analytics_repository=get_cohort_analytics_repo(),
    )


def get_process_warning_issued_use_case():
    from application.use_cases.process_warning_issued import (
        ProcessWarningIssuedUseCase,
    )

    return ProcessWarningIssuedUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_process_warning_resolved_use_case():
    from application.use_cases.process_warning_resolved import (
        ProcessWarningResolvedUseCase,
    )

    return ProcessWarningResolvedUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_process_student_promoted_use_case():
    from application.use_cases.process_student_promoted import (
        ProcessStudentPromotedUseCase,
    )

    return ProcessStudentPromotedUseCase(
        student_analytics_repository=get_student_analytics_repo(),
    )


def get_process_student_status_changed_use_case():
    from application.use_cases.process_student_status_changed import (
        ProcessStudentStatusChangedUseCase,
    )

    return ProcessStudentStatusChangedUseCase(
        student_analytics_repository=get_student_analytics_repo(),
        cohort_analytics_repository=get_cohort_analytics_repo(),
    )


# ── Scheduled Job Use Cases ─────────────────────────

def get_refresh_leaderboard_use_case():
    from application.use_cases.refresh_leaderboard import (
        RefreshLeaderboardUseCase,
    )

    return RefreshLeaderboardUseCase(
        student_analytics_repository=get_student_analytics_repo(),
        leaderboard_repository=get_leaderboard_repo(),
    )


def get_snapshot_historical_metrics_use_case():
    from application.use_cases.snapshot_historical_metrics import (
        SnapshotHistoricalMetricsUseCase,
    )

    return SnapshotHistoricalMetricsUseCase(
        student_analytics_repository=get_student_analytics_repo(),
        historical_metrics_repository=get_historical_metrics_repo(),
    )