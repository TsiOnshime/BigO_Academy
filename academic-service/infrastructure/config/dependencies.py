"""
infrastructure/config/dependencies.py — Academic Service

Wires every use case to its concrete adapter implementations. One factory
function per use case, following the exact pattern from the guide.

Repository/publisher instances are constructed once at module import time
and reused across factories — Django ORM repositories are stateless
(no per-request state), and KafkaEventPublisher holds a single
long-lived confluent_kafka.Producer per process, which is the correct
lifecycle for it (see kafka_event_publisher.py docstring).
"""
from adapters.outbound.messaging.kafka_event_publisher import KafkaEventPublisher
from adapters.outbound.messaging.kafka_event_publisher import ConsoleEventPublisher
from adapters.outbound.persistence.attendance_repo import DjangoAttendanceRepository
from adapters.outbound.persistence.cohort_repo import DjangoCohortRepository
from adapters.outbound.persistence.contest_repo import DjangoContestRepository
from adapters.outbound.persistence.curriculum_repo import DjangoCurriculumRepository
from adapters.outbound.persistence.mentorship_repo import DjangoMentorshipRepository
from adapters.outbound.persistence.progress_repo import DjangoProgressRepository
from adapters.outbound.persistence.student_repo import DjangoStudentRepository
from adapters.outbound.persistence.teacher_repo import DjangoTeacherRepository
from adapters.outbound.persistence.warning_repo import DjangoWarningRepository
from adapters.outbound.persistence.warning_rules_repo import DjangoWarningRulesRepository

from application.use_cases.attendance.edit_attendance import EditAttendanceUseCase
from application.use_cases.attendance.get_cohort_attendance import GetCohortAttendanceUseCase
from application.use_cases.attendance.get_session_attendance import GetSessionAttendanceUseCase
from application.use_cases.attendance.get_student_attendance import GetStudentAttendanceUseCase
from application.use_cases.attendance.submit_attendance import SubmitAttendanceUseCase

from application.use_cases.cohort.archive_cohort import ArchiveCohortUseCase
from application.use_cases.cohort.assign_student_to_cohort import AssignStudentToCohortUseCase
from application.use_cases.cohort.assign_teacher_to_cohort import AssignTeacherToCohortUseCase
from application.use_cases.cohort.create_cohort import CreateCohortUseCase
from application.use_cases.cohort.get_cohort import GetCohortUseCase
from application.use_cases.cohort.list_cohorts import ListCohortsUseCase
from application.use_cases.cohort.unassign_teacher_from_cohort import (
    UnassignTeacherFromCohortUseCase,
)
from application.use_cases.cohort.update_cohort import UpdateCohortUseCase

from application.use_cases.contest.create_contest import CreateContestUseCase
from application.use_cases.contest.get_contest import GetContestUseCase
from application.use_cases.contest.get_contest_results import GetContestResultsUseCase
from application.use_cases.contest.list_contests import ListContestsUseCase
from application.use_cases.contest.submit_contest_results import SubmitContestResultsUseCase

from application.use_cases.curriculum.add_problem import AddProblemUseCase
from application.use_cases.curriculum.create_topic import CreateTopicUseCase
from application.use_cases.curriculum.delete_problem import DeleteProblemUseCase
from application.use_cases.curriculum.delete_topic import DeleteTopicUseCase
from application.use_cases.curriculum.get_topic import GetTopicUseCase
from application.use_cases.curriculum.list_topics import ListTopicsUseCase
from application.use_cases.curriculum.reorder_topics import ReorderTopicsUseCase
from application.use_cases.curriculum.update_problem import UpdateProblemUseCase
from application.use_cases.curriculum.update_topic import UpdateTopicUseCase

from application.use_cases.mentorship.get_mentorship_session import GetMentorshipSessionUseCase
from application.use_cases.mentorship.list_mentorship_sessions import (
    ListMentorshipSessionsUseCase,
)
from application.use_cases.mentorship.schedule_mentorship import ScheduleMentorshipUseCase
from application.use_cases.mentorship.update_mentorship_session import (
    UpdateMentorshipSessionUseCase,
)

from application.use_cases.progress.get_student_progress import GetStudentProgressUseCase
from application.use_cases.progress.update_problem_progress import UpdateProblemProgressUseCase

from application.use_cases.student.create_student import CreateStudentUseCase
from application.use_cases.student.get_student import GetStudentUseCase
from application.use_cases.student.graduate_student import GraduateStudentUseCase
from application.use_cases.student.list_students import ListStudentsUseCase
from application.use_cases.student.promote_student import PromoteStudentUseCase
from application.use_cases.student.update_student import UpdateStudentUseCase
from application.use_cases.student.update_student_status import UpdateStudentStatusUseCase

from application.use_cases.teacher.activate_teacher import ActivateTeacherUseCase
from application.use_cases.teacher.create_teacher import CreateTeacherUseCase
from application.use_cases.teacher.deactivate_teacher import DeactivateTeacherUseCase
from application.use_cases.teacher.get_teacher import GetTeacherUseCase
from application.use_cases.teacher.list_teachers import ListTeachersUseCase
from application.use_cases.teacher.update_teacher import UpdateTeacherUseCase

from application.use_cases.warning.dismiss_warning import DismissWarningUseCase
from application.use_cases.warning.get_student_warnings import GetStudentWarningsUseCase
from application.use_cases.warning.get_warning_rules import GetWarningRulesUseCase
from application.use_cases.warning.list_escalated_warnings import ListEscalatedWarningsUseCase
from application.use_cases.warning.update_warning_rules import UpdateWarningRulesUseCase


# ── Shared adapter singletons ───────────────────────────────────────────
# Constructed once per process. Django ORM repos are stateless (each call
# opens/uses a connection from Django's connection pool), so sharing one
# instance across requests is safe and avoids needless re-instantiation.

_student_repository = DjangoStudentRepository()
_teacher_repository = DjangoTeacherRepository()
_cohort_repository = DjangoCohortRepository()
_curriculum_repository = DjangoCurriculumRepository()
_progress_repository = DjangoProgressRepository()
_attendance_repository = DjangoAttendanceRepository()
_contest_repository = DjangoContestRepository()
_warning_repository = DjangoWarningRepository()
_mentorship_repository = DjangoMentorshipRepository()
_warning_rules_repository = DjangoWarningRulesRepository()
_event_publisher = ConsoleEventPublisher()


# ── Student ──────────────────────────────────────────────────────────────

def get_create_student_use_case() -> CreateStudentUseCase:
    return CreateStudentUseCase(
        student_repository=_student_repository,
        cohort_repository=_cohort_repository,
        event_publisher=_event_publisher,
    )


def get_get_student_use_case() -> GetStudentUseCase:
    return GetStudentUseCase(student_repository=_student_repository)


def get_list_students_use_case() -> ListStudentsUseCase:
    return ListStudentsUseCase(student_repository=_student_repository)


def get_update_student_use_case() -> UpdateStudentUseCase:
    return UpdateStudentUseCase(student_repository=_student_repository)


def get_update_student_status_use_case() -> UpdateStudentStatusUseCase:
    return UpdateStudentStatusUseCase(
        student_repository=_student_repository,
        event_publisher=_event_publisher,
    )


def get_promote_student_use_case() -> PromoteStudentUseCase:
    return PromoteStudentUseCase(
        student_repository=_student_repository,
        event_publisher=_event_publisher,
    )


def get_graduate_student_use_case() -> GraduateStudentUseCase:
    return GraduateStudentUseCase(
        student_repository=_student_repository,
        event_publisher=_event_publisher,
    )


# ── Teacher ──────────────────────────────────────────────────────────────

def get_create_teacher_use_case() -> CreateTeacherUseCase:
    return CreateTeacherUseCase(
        teacher_repository=_teacher_repository,
        event_publisher=_event_publisher,
    )


def get_get_teacher_use_case() -> GetTeacherUseCase:
    return GetTeacherUseCase(teacher_repository=_teacher_repository)


def get_list_teachers_use_case() -> ListTeachersUseCase:
    return ListTeachersUseCase(teacher_repository=_teacher_repository)


def get_update_teacher_use_case() -> UpdateTeacherUseCase:
    return UpdateTeacherUseCase(teacher_repository=_teacher_repository)


def get_activate_teacher_use_case() -> ActivateTeacherUseCase:
    return ActivateTeacherUseCase(
        teacher_repository=_teacher_repository,
        event_publisher=_event_publisher,
    )


def get_deactivate_teacher_use_case() -> DeactivateTeacherUseCase:
    return DeactivateTeacherUseCase(
        teacher_repository=_teacher_repository,
        event_publisher=_event_publisher,
    )


# ── Cohort ───────────────────────────────────────────────────────────────

def get_create_cohort_use_case() -> CreateCohortUseCase:
    return CreateCohortUseCase(
        cohort_repository=_cohort_repository,
        event_publisher=_event_publisher,
    )


def get_get_cohort_use_case() -> GetCohortUseCase:
    return GetCohortUseCase(cohort_repository=_cohort_repository)


def get_list_cohorts_use_case() -> ListCohortsUseCase:
    return ListCohortsUseCase(cohort_repository=_cohort_repository)


def get_update_cohort_use_case() -> UpdateCohortUseCase:
    return UpdateCohortUseCase(
        cohort_repository=_cohort_repository,
        event_publisher=_event_publisher,
    )


def get_archive_cohort_use_case() -> ArchiveCohortUseCase:
    return ArchiveCohortUseCase(
        cohort_repository=_cohort_repository,
        event_publisher=_event_publisher,
    )


def get_assign_student_to_cohort_use_case() -> AssignStudentToCohortUseCase:
    return AssignStudentToCohortUseCase(
        cohort_repository=_cohort_repository,
        student_repository=_student_repository,
    )


def get_assign_teacher_to_cohort_use_case() -> AssignTeacherToCohortUseCase:
    return AssignTeacherToCohortUseCase(
        cohort_repository=_cohort_repository,
        teacher_repository=_teacher_repository,
        event_publisher=_event_publisher,
    )


def get_unassign_teacher_from_cohort_use_case() -> UnassignTeacherFromCohortUseCase:
    return UnassignTeacherFromCohortUseCase(
        cohort_repository=_cohort_repository,
        teacher_repository=_teacher_repository,
        event_publisher=_event_publisher,
    )


# ── Curriculum (Topics + Problems) ─────────────────────────────────────

def get_create_topic_use_case() -> CreateTopicUseCase:
    return CreateTopicUseCase(
        curriculum_repository=_curriculum_repository,
        cohort_repository=_cohort_repository,
    )


def get_get_topic_use_case() -> GetTopicUseCase:
    return GetTopicUseCase(curriculum_repository=_curriculum_repository)


def get_list_topics_use_case() -> ListTopicsUseCase:
    return ListTopicsUseCase(curriculum_repository=_curriculum_repository)


def get_update_topic_use_case() -> UpdateTopicUseCase:
    return UpdateTopicUseCase(curriculum_repository=_curriculum_repository)


def get_delete_topic_use_case() -> DeleteTopicUseCase:
    return DeleteTopicUseCase(curriculum_repository=_curriculum_repository)


def get_reorder_topics_use_case() -> ReorderTopicsUseCase:
    return ReorderTopicsUseCase(curriculum_repository=_curriculum_repository)


def get_add_problem_use_case() -> AddProblemUseCase:
    return AddProblemUseCase(curriculum_repository=_curriculum_repository)


def get_update_problem_use_case() -> UpdateProblemUseCase:
    return UpdateProblemUseCase(curriculum_repository=_curriculum_repository)


def get_delete_problem_use_case() -> DeleteProblemUseCase:
    return DeleteProblemUseCase(curriculum_repository=_curriculum_repository)


# ── Progress ─────────────────────────────────────────────────────────────

def get_update_problem_progress_use_case() -> UpdateProblemProgressUseCase:
    return UpdateProblemProgressUseCase(
        student_repository=_student_repository,
        curriculum_repository=_curriculum_repository,
        progress_repository=_progress_repository,
        event_publisher=_event_publisher,
    )


def get_get_student_progress_use_case() -> GetStudentProgressUseCase:
    return GetStudentProgressUseCase(
        student_repository=_student_repository,
        progress_repository=_progress_repository,
    )


# ── Attendance ───────────────────────────────────────────────────────────

def get_submit_attendance_use_case() -> SubmitAttendanceUseCase:
    return SubmitAttendanceUseCase(
        attendance_repository=_attendance_repository,
        cohort_repository=_cohort_repository,
        event_publisher=_event_publisher,
    )


def get_edit_attendance_use_case() -> EditAttendanceUseCase:
    return EditAttendanceUseCase(
        attendance_repository=_attendance_repository,
        event_publisher=_event_publisher,
    )


def get_get_session_attendance_use_case() -> GetSessionAttendanceUseCase:
    return GetSessionAttendanceUseCase(attendance_repository=_attendance_repository)


def get_get_cohort_attendance_use_case() -> GetCohortAttendanceUseCase:
    return GetCohortAttendanceUseCase(
        cohort_repository=_cohort_repository,
        attendance_repository=_attendance_repository,
    )


def get_get_student_attendance_use_case() -> GetStudentAttendanceUseCase:
    return GetStudentAttendanceUseCase(
        student_repository=_student_repository,
        attendance_repository=_attendance_repository,
    )


# ── Contest ──────────────────────────────────────────────────────────────

def get_create_contest_use_case() -> CreateContestUseCase:
    return CreateContestUseCase(
        contest_repository=_contest_repository,
        cohort_repository=_cohort_repository,
    )


def get_get_contest_use_case() -> GetContestUseCase:
    return GetContestUseCase(contest_repository=_contest_repository)


def get_list_contests_use_case() -> ListContestsUseCase:
    return ListContestsUseCase(contest_repository=_contest_repository)


def get_submit_contest_results_use_case() -> SubmitContestResultsUseCase:
    return SubmitContestResultsUseCase(
        contest_repository=_contest_repository,
        event_publisher=_event_publisher,
    )


def get_get_contest_results_use_case() -> GetContestResultsUseCase:
    return GetContestResultsUseCase(contest_repository=_contest_repository)


# ── Warning ──────────────────────────────────────────────────────────────

def get_dismiss_warning_use_case() -> DismissWarningUseCase:
    return DismissWarningUseCase(
        warning_repository=_warning_repository,
        event_publisher=_event_publisher,
    )


def get_get_student_warnings_use_case() -> GetStudentWarningsUseCase:
    return GetStudentWarningsUseCase(
        student_repository=_student_repository,
        warning_repository=_warning_repository,
    )


def get_list_escalated_warnings_use_case() -> ListEscalatedWarningsUseCase:
    return ListEscalatedWarningsUseCase(warning_repository=_warning_repository)


def get_get_warning_rules_use_case() -> GetWarningRulesUseCase:
    return GetWarningRulesUseCase(warning_rules_repository=_warning_rules_repository)


def get_update_warning_rules_use_case() -> UpdateWarningRulesUseCase:
    return UpdateWarningRulesUseCase(warning_rules_repository=_warning_rules_repository)


# ── Mentorship ───────────────────────────────────────────────────────────

def get_schedule_mentorship_use_case() -> ScheduleMentorshipUseCase:
    return ScheduleMentorshipUseCase(
        mentorship_repository=_mentorship_repository,
        student_repository=_student_repository,
        teacher_repository=_teacher_repository,
    )


def get_get_mentorship_session_use_case() -> GetMentorshipSessionUseCase:
    return GetMentorshipSessionUseCase(mentorship_repository=_mentorship_repository)


def get_list_mentorship_sessions_use_case() -> ListMentorshipSessionsUseCase:
    return ListMentorshipSessionsUseCase(mentorship_repository=_mentorship_repository)


def get_update_mentorship_session_use_case() -> UpdateMentorshipSessionUseCase:
    return UpdateMentorshipSessionUseCase(mentorship_repository=_mentorship_repository)

# ── Read-only repository accessors ──────────────────────────────────────
# Added for the REST views layer (adapters/inbound/rest/views/). A few
# response schemas need a "view-supplied" denormalized field that has no
# use case of its own -- e.g. StudentResponse.cohortName, ContestResults
# Response.contestTitle, ProblemProgressResponse.problemTitle (see the
# docstrings in adapters/inbound/rest/serializers/*.py, which explicitly
# call out "the view looks this up via <x>_repository"). Rather than
# have views import the concrete Django*Repository classes directly
# (which would bypass this composition root), the views ask for the
# already-constructed singleton through these thin accessors. This does
# NOT go through a use case because there's no business rule involved --
# it's a plain read used only to render a response field.
def get_student_repository():
    return _student_repository


def get_teacher_repository():
    return _teacher_repository


def get_cohort_repository():
    return _cohort_repository


def get_curriculum_repository():
    return _curriculum_repository