"""
adapters/inbound/rest/serializers/__init__.py — Academic Service

Re-exports every serializer so `from adapters.inbound.rest.serializers
import X` keeps working exactly like a single serializers.py would,
matching the class names from the collaboration guide's table.
"""
from .student import (
    CreateStudentSerializer,
    UpdateStudentSerializer,
    UpdateStudentStatusSerializer,
    StudentResponseSerializer,
    StudentListResponseSerializer,
    AssignStudentSerializer,
)
from .teacher import (
    CreateTeacherSerializer,
    UpdateTeacherSerializer,
    TeacherResponseSerializer,
    TeacherListResponseSerializer,
    AssignTeacherSerializer,
)
from .cohort import (
    CreateCohortSerializer,
    UpdateCohortSerializer,
    CohortResponseSerializer,
    CohortListResponseSerializer,
)
from .curriculum import (
    CreateTopicSerializer,
    UpdateTopicSerializer,
    ReorderTopicsSerializer,
    TopicResponseSerializer,
    TopicListResponseSerializer,
    CreateProblemSerializer,
    UpdateProblemSerializer,
    ProblemResponseSerializer,
    ProblemListResponseSerializer,
)
from .progress import (
    UpdateProgressSerializer,
    ProblemProgressResponseSerializer,
    TopicProgressSummarySerializer,
    ProgressSheetResponseSerializer,
)
from .attendance import (
    SubmitAttendanceSerializer,
    EditAttendanceSerializer,
    AttendanceRecordSerializer,
    AttendanceSessionResponseSerializer,
    AttendanceHistoryEntrySerializer,
    StudentAttendanceResponseSerializer,
    StudentAttendanceSummarySerializer,
    CohortAttendanceResponseSerializer,
)
from .contest import (
    CreateContestSerializer,
    SubmitContestResultsSerializer,
    ContestResponseSerializer,
    ContestListResponseSerializer,
    ContestParticipantResultSerializer,
    ContestResultsResponseSerializer,
)
from .warning import (
    DismissWarningSerializer,
    UpdateWarningRulesSerializer,
    WarningResponseSerializer,
    WarningListResponseSerializer,
    EscalatedStudentSerializer,
    EscalatedStudentListResponseSerializer,
    WarningRulesResponseSerializer,
)
from .mentorship import (
    CreateMentorshipSessionSerializer,
    UpdateMentorshipSessionSerializer,
    MentorshipSessionResponseSerializer,
    MentorshipSessionListResponseSerializer,
)
from .common import PageMetaSerializer, EnumValueField

__all__ = [
    # student
    "CreateStudentSerializer", "UpdateStudentSerializer",
    "UpdateStudentStatusSerializer", "StudentResponseSerializer",
    "StudentListResponseSerializer", "AssignStudentSerializer",
    # teacher
    "CreateTeacherSerializer", "UpdateTeacherSerializer",
    "TeacherResponseSerializer", "TeacherListResponseSerializer",
    "AssignTeacherSerializer",
    # cohort
    "CreateCohortSerializer", "UpdateCohortSerializer",
    "CohortResponseSerializer", "CohortListResponseSerializer",
    # curriculum
    "CreateTopicSerializer", "UpdateTopicSerializer", "ReorderTopicsSerializer",
    "TopicResponseSerializer", "TopicListResponseSerializer",
    "CreateProblemSerializer", "UpdateProblemSerializer",
    "ProblemResponseSerializer", "ProblemListResponseSerializer",
    # progress
    "UpdateProgressSerializer", "ProblemProgressResponseSerializer",
    "TopicProgressSummarySerializer", "ProgressSheetResponseSerializer",
    # attendance
    "SubmitAttendanceSerializer", "EditAttendanceSerializer",
    "AttendanceRecordSerializer", "AttendanceSessionResponseSerializer",
    "AttendanceHistoryEntrySerializer", "StudentAttendanceResponseSerializer",
    "StudentAttendanceSummarySerializer", "CohortAttendanceResponseSerializer",
    # contest
    "CreateContestSerializer", "SubmitContestResultsSerializer",
    "ContestResponseSerializer", "ContestListResponseSerializer",
    "ContestParticipantResultSerializer", "ContestResultsResponseSerializer",
    # warning
    "DismissWarningSerializer", "UpdateWarningRulesSerializer",
    "WarningResponseSerializer", "WarningListResponseSerializer",
    "EscalatedStudentSerializer", "EscalatedStudentListResponseSerializer",
    "WarningRulesResponseSerializer",
    # mentorship
    "CreateMentorshipSessionSerializer", "UpdateMentorshipSessionSerializer",
    "MentorshipSessionResponseSerializer", "MentorshipSessionListResponseSerializer",
    # common
    "PageMetaSerializer", "EnumValueField",
]