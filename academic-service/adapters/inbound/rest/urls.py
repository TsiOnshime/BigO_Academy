"""
adapters/inbound/rest/urls.py — Academic Service

Maps URL paths to view classes, mounted under the api/v1/ prefix added
in config/urls.py (matching the convention used by auth-service).

Each unique route appears exactly ONCE below. Where a resource needs
both e.g. GET+POST or GET+PATCH on the identical path, that's handled
by a single view class defining both methods (StudentListCreateView,
CohortDetailView, WarningRulesView, etc.) — Django's URL resolver
dispatches purely on the path pattern, not the HTTP verb, so two
separate path() entries with the same route would always match
whichever came first regardless of method.
"""
from django.urls import path

from .views import (
    ActivateTeacherView,
    AddProblemView,
    ArchiveCohortView,
    AssignStudentToCohortView,
    AssignTeacherToCohortView,
    CohortDetailView,
    CohortListCreateView,
    ContestListCreateView,
    ContestResultsView,
    DeactivateTeacherView,
    DismissWarningView,
    GetCohortAttendanceView,
    GetContestView,
    GetStudentAttendanceView,
    GetStudentProgressView,
    GetStudentWarningsView,
    GlobalContestListCreateView,
    GraduateStudentView,
    ListEscalatedWarningsView,
    MentorshipSessionDetailView,
    MentorshipSessionListCreateView,
    ProblemDetailView,
    PromoteStudentView,
    ReorderTopicsView,
    SessionAttendanceDetailView,
    StudentDetailView,
    StudentListCreateView,
    SubmitAttendanceView,
    TeacherDetailView,
    TeacherListCreateView,
    TopicDetailView,
    TopicListCreateView,
    UnassignTeacherFromCohortView,
    UpdateProblemProgressView,
    UpdateStudentStatusView,
    WarningRulesView,
)

urlpatterns = [
    # ── Students ──────────────────────────────────────────────────────
    path("students/", StudentListCreateView.as_view(), name="students-list-create"),
    path(
        "students/<uuid:student_id>/",
        StudentDetailView.as_view(),
        name="student-detail",
    ),
    path(
        "students/<uuid:student_id>/status/",
        UpdateStudentStatusView.as_view(),
        name="update-student-status",
    ),
    path(
        "students/<uuid:student_id>/promote/",
        PromoteStudentView.as_view(),
        name="promote-student",
    ),
    path(
        "students/<uuid:student_id>/graduate/",
        GraduateStudentView.as_view(),
        name="graduate-student",
    ),
    path(
        "students/<uuid:student_id>/attendance/",
        GetStudentAttendanceView.as_view(),
        name="get-student-attendance",
    ),
    path(
        "students/<uuid:student_id>/progress/",
        GetStudentProgressView.as_view(),
        name="get-student-progress",
    ),
    path(
        "students/<uuid:student_id>/progress/<uuid:problem_id>/",
        UpdateProblemProgressView.as_view(),
        name="update-problem-progress",
    ),
    path(
        "students/<uuid:student_id>/warnings/",
        GetStudentWarningsView.as_view(),
        name="get-student-warnings",
    ),

    # ── Teachers ──────────────────────────────────────────────────────
    path("teachers/", TeacherListCreateView.as_view(), name="teachers-list-create"),
    path(
        "teachers/<uuid:teacher_id>/",
        TeacherDetailView.as_view(),
        name="teacher-detail",
    ),
    path(
        "teachers/<uuid:teacher_id>/activate/",
        ActivateTeacherView.as_view(),
        name="activate-teacher",
    ),
    path(
        "teachers/<uuid:teacher_id>/deactivate/",
        DeactivateTeacherView.as_view(),
        name="deactivate-teacher",
    ),

    # ── Cohorts ───────────────────────────────────────────────────────
    path("cohorts/", CohortListCreateView.as_view(), name="cohorts-list-create"),
    path(
        "cohorts/<uuid:cohort_id>/",
        CohortDetailView.as_view(),
        name="cohort-detail",
    ),
    path(
        "cohorts/<uuid:cohort_id>/archive/",
        ArchiveCohortView.as_view(),
        name="archive-cohort",
    ),
    path(
        "cohorts/<uuid:cohort_id>/students/",
        AssignStudentToCohortView.as_view(),
        name="assign-student-to-cohort",
    ),
    path(
        "cohorts/<uuid:cohort_id>/teachers/",
        AssignTeacherToCohortView.as_view(),
        name="assign-teacher-to-cohort",
    ),
    path(
        "cohorts/<uuid:cohort_id>/teachers/<uuid:teacher_id>/",
        UnassignTeacherFromCohortView.as_view(),
        name="unassign-teacher-from-cohort",
    ),
    path(
        "cohorts/<uuid:cohort_id>/attendance/",
        GetCohortAttendanceView.as_view(),
        name="get-cohort-attendance",
    ),

    # ── Curriculum (topics + problems) ───────────────────────────────
    path(
        "cohorts/<uuid:cohort_id>/topics/",
        TopicListCreateView.as_view(),
        name="topics-list-create",
    ),
    path("topics/<uuid:topic_id>/", TopicDetailView.as_view(), name="topic-detail"),
    path("topics/reorder/", ReorderTopicsView.as_view(), name="reorder-topics"),
    path(
        "topics/<uuid:topic_id>/problems/",
        AddProblemView.as_view(),
        name="add-problem",
    ),
    path(
        "problems/<uuid:problem_id>/",
        ProblemDetailView.as_view(),
        name="problem-detail",
    ),

    # ── Attendance ────────────────────────────────────────────────────
    path(
        "attendance/sessions/",
        SubmitAttendanceView.as_view(),
        name="submit-attendance",
    ),
    path(
        "attendance/sessions/<uuid:session_id>/",
        SessionAttendanceDetailView.as_view(),
        name="session-attendance-detail",
    ),

    # ── Contests ──────────────────────────────────────────────────────
    path("contests/", GlobalContestListCreateView.as_view(), name="global-contests-list-create"),
    path(
        "cohorts/<uuid:cohort_id>/contests/",
        ContestListCreateView.as_view(),
        name="contests-list-create",
    ),
    path(
        "contests/<uuid:contest_id>/",
        GetContestView.as_view(),
        name="get-contest",
    ),
    path(
        "contests/<uuid:contest_id>/results/",
        ContestResultsView.as_view(),
        name="contest-results",
    ),

    # ── Mentorship ────────────────────────────────────────────────────
    path(
        "mentorship-sessions/",
        MentorshipSessionListCreateView.as_view(),
        name="mentorship-sessions-list-create",
    ),
    path(
        "mentorship-sessions/<uuid:session_id>/",
        MentorshipSessionDetailView.as_view(),
        name="mentorship-session-detail",
    ),

    # ── Warnings ──────────────────────────────────────────────────────
    path(
        "warnings/<uuid:warning_id>/dismiss/",
        DismissWarningView.as_view(),
        name="dismiss-warning",
    ),
    path(
        "warnings/escalated/",
        ListEscalatedWarningsView.as_view(),
        name="list-escalated-warnings",
    ),
    path("warnings/rules/", WarningRulesView.as_view(), name="warning-rules"),
]