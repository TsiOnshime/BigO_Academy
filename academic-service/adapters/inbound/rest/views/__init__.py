"""
adapters/inbound/rest/views/__init__.py — Academic Service

Re-exports every view so `from adapters.inbound.rest.views import X`
works exactly like a single views.py would, mirroring auth-service's
views/__init__.py.
"""
from .student_views import (
    GraduateStudentView,
    PromoteStudentView,
    StudentDetailView,
    StudentListCreateView,
    UpdateStudentStatusView,
)
from .teacher_views import (
    ActivateTeacherView,
    DeactivateTeacherView,
    TeacherDetailView,
    TeacherListCreateView,
)
from .cohort_views import (
    ArchiveCohortView,
    AssignStudentToCohortView,
    AssignTeacherToCohortView,
    CohortDetailView,
    CohortListCreateView,
    GetCohortAttendanceView,
    UnassignTeacherFromCohortView,
)
from .curriculum_views import (
    AddProblemView,
    ProblemDetailView,
    ReorderTopicsView,
    TopicDetailView,
    TopicListCreateView,
)
from .attendance_views import (
    GetStudentAttendanceView,
    SessionAttendanceDetailView,
    SubmitAttendanceView,
)
from .contest_views import (
    ContestListCreateView,
    ContestResultsView,
    GetContestView,
    GlobalContestListCreateView,
)
from .mentorship_views import (
    MentorshipSessionDetailView,
    MentorshipSessionListCreateView,
)
from .progress_views import GetStudentProgressView, UpdateProblemProgressView
from .warning_views import (
    DismissWarningView,
    GetStudentWarningsView,
    ListEscalatedWarningsView,
    WarningRulesView,
)

__all__ = [
    # student
    "GraduateStudentView", "PromoteStudentView", "StudentDetailView",
    "StudentListCreateView", "UpdateStudentStatusView",
    # teacher
    "ActivateTeacherView", "DeactivateTeacherView", "TeacherDetailView",
    "TeacherListCreateView",
    # cohort
    "ArchiveCohortView", "AssignStudentToCohortView",
    "AssignTeacherToCohortView", "CohortDetailView", "CohortListCreateView",
    "GetCohortAttendanceView", "UnassignTeacherFromCohortView",
    # curriculum
    "AddProblemView", "ProblemDetailView", "ReorderTopicsView",
    "TopicDetailView", "TopicListCreateView",
    # attendance
    "GetStudentAttendanceView", "SessionAttendanceDetailView",
    "SubmitAttendanceView",
    # contest
    "ContestListCreateView", "ContestResultsView", "GetContestView",
    # mentorship
    "MentorshipSessionDetailView", "MentorshipSessionListCreateView",
    # progress
    "GetStudentProgressView", "UpdateProblemProgressView",
    # warning
    "DismissWarningView", "GetStudentWarningsView",
    "ListEscalatedWarningsView", "WarningRulesView",
]