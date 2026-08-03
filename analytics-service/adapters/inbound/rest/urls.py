from django.urls import path

from adapters.inbound.rest.views import (
    StudentAnalyticsView,
    StudentAnalyticsSummaryView,
    StudentHistoryView,
    GlobalLeaderboardView,
    CohortLeaderboardView,
    TeacherAnalyticsView,
    PlatformAnalyticsView,
    AdminCohortAnalyticsView,
    AnalyticsReportView,
)

urlpatterns = [
    # Student analytics
    path(
        "analytics/students/<uuid:student_id>/",
        StudentAnalyticsView.as_view(),
    ),
    path(
        "analytics/students/<uuid:student_id>/summary/",
        StudentAnalyticsSummaryView.as_view(),
    ),
    path(
        "analytics/students/<uuid:student_id>/history/",
        StudentHistoryView.as_view(),
    ),

    # Leaderboard
    path(
        "analytics/leaderboard/",
        GlobalLeaderboardView.as_view(),
    ),
    path(
        "analytics/leaderboard/cohorts/<uuid:cohort_id>/",
        CohortLeaderboardView.as_view(),
    ),

    # Teacher analytics
    path(
        "analytics/teachers/<uuid:teacher_id>/",
        TeacherAnalyticsView.as_view(),
    ),

    # Admin analytics
    path(
        "analytics/admin/platform/",
        PlatformAnalyticsView.as_view(),
    ),
    path(
        "analytics/admin/cohorts/<uuid:cohort_id>/",
        AdminCohortAnalyticsView.as_view(),
    ),
    path(
        "analytics/admin/reports/<str:report_type>/",
        AnalyticsReportView.as_view(),
    ),
]