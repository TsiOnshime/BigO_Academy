from uuid import UUID
from datetime import date
from typing import Optional

from domain.models import (
    Student, Teacher, Cohort, Topic, Problem,
    ProblemProgress, ClassSession, AttendanceRecord,
    Contest, ContestResult, Warning, MentorshipSession,
)
from domain.enums import (
    StudentStatus, TeacherStatus, CohortStatus,
    ContestStatus, WarningStatus, YearPhase,
)
from application.ports.outbound.student_repository import StudentRepositoryPort
from application.ports.outbound.teacher_repository import TeacherRepositoryPort
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort
from application.ports.outbound.progress_repository import ProgressRepositoryPort
from application.ports.outbound.attendance_repository import AttendanceRepositoryPort
from application.ports.outbound.contest_repository import ContestRepositoryPort
from application.ports.outbound.warning_repository import WarningRepositoryPort
from application.ports.outbound.mentorship_repository import MentorshipRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort
from application.ports.outbound.warning_rules_repository import (
    WarningRulesRepositoryPort, WarningRules,
)


class FakeStudentRepository(StudentRepositoryPort):

    def __init__(self):
        self._store: dict[UUID, Student] = {}

    def save(self, student: Student) -> Student:
        self._store[student.id] = student
        return student

    def find_by_id(self, student_id: UUID) -> Optional[Student]:
        return self._store.get(student_id)

    def find_by_user_id(self, user_id: UUID) -> Optional[Student]:
        for s in self._store.values():
            if s.user_id == user_id:
                return s
        return None

    def find_all(self, cohort_id=None, status=None) -> list[Student]:
        results = list(self._store.values())
        if cohort_id is not None:
            results = [s for s in results if s.cohort_id == cohort_id]
        if status is not None:
            results = [s for s in results if s.status == status]
        return results

    def exists_by_user_id(self, user_id: UUID) -> bool:
        return self.find_by_user_id(user_id) is not None


class FakeTeacherRepository(TeacherRepositoryPort):

    def __init__(self):
        self._store: dict[UUID, Teacher] = {}

    def save(self, teacher: Teacher) -> Teacher:
        self._store[teacher.id] = teacher
        return teacher

    def find_by_id(self, teacher_id: UUID) -> Optional[Teacher]:
        return self._store.get(teacher_id)

    def find_by_user_id(self, user_id: UUID) -> Optional[Teacher]:
        for t in self._store.values():
            if t.user_id == user_id:
                return t
        return None

    def find_all(self, status=None) -> list[Teacher]:
        results = list(self._store.values())
        if status is not None:
            results = [t for t in results if t.status == status]
        return results

    def exists_by_user_id(self, user_id: UUID) -> bool:
        return self.find_by_user_id(user_id) is not None


class FakeCohortRepository(CohortRepositoryPort):

    def __init__(self):
        self._store: dict[UUID, Cohort] = {}
        self._student_assignments: dict[UUID, set[UUID]] = {}
        self._teacher_assignments: dict[UUID, set[UUID]] = {}

    def save(self, cohort: Cohort) -> Cohort:
        self._store[cohort.id] = cohort
        return cohort

    def find_by_id(self, cohort_id: UUID) -> Optional[Cohort]:
        return self._store.get(cohort_id)

    def find_all(self, status=None) -> list[Cohort]:
        results = list(self._store.values())
        if status is not None:
            results = [c for c in results if c.status == status]
        return results

    def assign_student(self, cohort_id: UUID, student_id: UUID) -> None:
        if cohort_id not in self._student_assignments:
            self._student_assignments[cohort_id] = set()
        self._student_assignments[cohort_id].add(student_id)
        # Update count
        cohort = self._store.get(cohort_id)
        if cohort:
            cohort.enrolled_student_count += 1

    def unassign_student(self, cohort_id: UUID, student_id: UUID) -> None:
        if cohort_id in self._student_assignments:
            self._student_assignments[cohort_id].discard(student_id)
        cohort = self._store.get(cohort_id)
        if cohort and cohort.enrolled_student_count > 0:
            cohort.enrolled_student_count -= 1

    def assign_teacher(self, cohort_id: UUID, teacher_id: UUID) -> None:
        if cohort_id not in self._teacher_assignments:
            self._teacher_assignments[cohort_id] = set()
        self._teacher_assignments[cohort_id].add(teacher_id)
        cohort = self._store.get(cohort_id)
        if cohort:
            cohort.teacher_count += 1

    def unassign_teacher(self, cohort_id: UUID, teacher_id: UUID) -> None:
        if cohort_id in self._teacher_assignments:
            self._teacher_assignments[cohort_id].discard(teacher_id)
        cohort = self._store.get(cohort_id)
        if cohort and cohort.teacher_count > 0:
            cohort.teacher_count -= 1

    def student_in_cohort(self, cohort_id: UUID, student_id: UUID) -> bool:
        return student_id in self._student_assignments.get(cohort_id, set())

    def teacher_in_cohort(self, cohort_id: UUID, teacher_id: UUID) -> bool:
        return teacher_id in self._teacher_assignments.get(cohort_id, set())


class FakeCurriculumRepository(CurriculumRepositoryPort):

    def __init__(self):
        self._topics: dict[UUID, Topic] = {}
        self._problems: dict[UUID, Problem] = {}

    def save_topic(self, topic: Topic) -> Topic:
        self._topics[topic.id] = topic
        return topic

    def find_topic_by_id(self, topic_id: UUID) -> Optional[Topic]:
        return self._topics.get(topic_id)

    def find_topics_by_cohort(self, cohort_id, year_phase=None) -> list[Topic]:
        results = [
            t for t in self._topics.values()
            if t.curriculum_id == cohort_id
        ]
        if year_phase is not None:
            results = [t for t in results if t.year_phase == year_phase]
        return sorted(results, key=lambda t: t.display_order)

    def delete_topic(self, topic_id: UUID) -> None:
        self._topics.pop(topic_id, None)
        # Cascade delete problems
        to_delete = [
            pid for pid, p in self._problems.items()
            if p.topic_id == topic_id
        ]
        for pid in to_delete:
            self._problems.pop(pid)

    def reorder_topics(self, ordered_topic_ids: list[UUID]) -> None:
        for order, topic_id in enumerate(ordered_topic_ids):
            if topic_id in self._topics:
                self._topics[topic_id].display_order = order

    def save_problem(self, problem: Problem) -> Problem:
        self._problems[problem.id] = problem
        return problem

    def find_problem_by_id(self, problem_id: UUID) -> Optional[Problem]:
        return self._problems.get(problem_id)

    def find_problems_by_topic(self, topic_id: UUID) -> list[Problem]:
        return [p for p in self._problems.values() if p.topic_id == topic_id]

    def delete_problem(self, problem_id: UUID) -> None:
        self._problems.pop(problem_id, None)


class FakeProgressRepository(ProgressRepositoryPort):

    def __init__(self):
        self._store: dict[tuple, ProblemProgress] = {}

    def save(self, progress: ProblemProgress) -> ProblemProgress:
        key = (progress.student_id, progress.problem_id)
        self._store[key] = progress
        return progress

    def find_by_student_and_problem(
        self, student_id: UUID, problem_id: UUID
    ) -> Optional[ProblemProgress]:
        return self._store.get((student_id, problem_id))

    def find_all_by_student(
        self, student_id: UUID, topic_id=None
    ) -> list[ProblemProgress]:
        return [
            p for (sid, _), p in self._store.items()
            if sid == student_id
        ]

    def count_solved_by_student(self, student_id: UUID) -> int:
        return sum(
            1 for (sid, _), p in self._store.items()
            if sid == student_id and p.solved
        )


class FakeAttendanceRepository(AttendanceRepositoryPort):

    def __init__(self):
        self._sessions: dict[UUID, ClassSession] = {}

    def save_session(self, session: ClassSession) -> ClassSession:
        self._sessions[session.id] = session
        return session

    def find_session_by_id(self, session_id: UUID) -> Optional[ClassSession]:
        return self._sessions.get(session_id)

    def find_sessions_by_cohort(
        self, cohort_id, from_date=None, to_date=None
    ) -> list[ClassSession]:
        return [
            s for s in self._sessions.values()
            if s.cohort_id == cohort_id
        ]

    def find_student_attendance(
        self, student_id, from_date=None, to_date=None
    ) -> list[AttendanceRecord]:
        records = []
        for session in self._sessions.values():
            for record in session.records:
                if record.student_id == student_id:
                    records.append(record)
        return records

    def calculate_attendance_percentage(self, student_id: UUID) -> float:
        total = 0
        present = 0
        for session in self._sessions.values():
            for record in session.records:
                if record.student_id == student_id:
                    total += 1
                    if record.status.value == "PRESENT":
                        present += 1
        if total == 0:
            return 0.0
        return round((present / total) * 100, 2)


class FakeContestRepository(ContestRepositoryPort):

    def __init__(self):
        self._store: dict[UUID, Contest] = {}
        self._results: dict[UUID, list[ContestResult]] = {}

    def save(self, contest: Contest) -> Contest:
        self._store[contest.id] = contest
        return contest

    def find_by_id(self, contest_id: UUID) -> Optional[Contest]:
        return self._store.get(contest_id)

    def find_all_by_cohort(self, cohort_id, status=None) -> list[Contest]:
        results = [
            c for c in self._store.values()
            if c.cohort_id == cohort_id
        ]
        if status is not None:
            results = [c for c in results if c.status == status]
        return results

    def save_results(
        self, contest_id: UUID, results: list[ContestResult]
    ) -> None:
        self._results[contest_id] = results

    def find_results_by_contest(
        self, contest_id: UUID
    ) -> list[ContestResult]:
        return self._results.get(contest_id, [])

    def has_results(self, contest_id: UUID) -> bool:
        return contest_id in self._results and len(
            self._results[contest_id]
        ) > 0


class FakeWarningRepository(WarningRepositoryPort):

    def __init__(self):
        self._store: dict[UUID, Warning] = {}

    def save(self, warning: Warning) -> Warning:
        self._store[warning.id] = warning
        return warning

    def find_by_id(self, warning_id: UUID) -> Optional[Warning]:
        return self._store.get(warning_id)

    def find_by_student(self, student_id: UUID) -> list[Warning]:
        return [
            w for w in self._store.values()
            if w.student_id == student_id
        ]

    def count_active_warnings(self, student_id: UUID) -> int:
        return sum(
            1 for w in self._store.values()
            if w.student_id == student_id
            and w.status == WarningStatus.ACTIVE
        )

    def find_escalated(self, cohort_id=None) -> list[Warning]:
        return [
            w for w in self._store.values()
            if w.status == WarningStatus.ESCALATED
        ]


class FakeMentorshipRepository(MentorshipRepositoryPort):

    def __init__(self):
        self._store: dict[UUID, MentorshipSession] = {}

    def save(self, session: MentorshipSession) -> MentorshipSession:
        self._store[session.id] = session
        return session

    def find_by_id(self, session_id: UUID) -> Optional[MentorshipSession]:
        return self._store.get(session_id)

    def find_by_student(self, student_id: UUID) -> list[MentorshipSession]:
        return [
            s for s in self._store.values()
            if s.student_id == student_id
        ]

    def find_by_teacher(self, teacher_id: UUID) -> list[MentorshipSession]:
        return [
            s for s in self._store.values()
            if s.teacher_id == teacher_id
        ]


class FakeEventPublisher(EventPublisherPort):
    """
    Records all published events so tests can verify
    the right events were fired.
    """

    def __init__(self):
        self.published_events: list[dict] = []

    def _record(self, event_type: str, **kwargs):
        self.published_events.append({
            "type": event_type,
            **kwargs
        })

    def get_events_of_type(self, event_type: str) -> list[dict]:
        return [e for e in self.published_events if e["type"] == event_type]

    def publish_student_created(self, student):
        self._record("student_created", student_id=student.id)

    def publish_student_status_changed(self, student, old_status):
        self._record("student_status_changed",
                     student_id=student.id,
                     old_status=old_status,
                     new_status=student.status.value)

    def publish_student_promoted(self, student):
        self._record("student_promoted", student_id=student.id)

    def publish_student_graduated(self, student):
        self._record("student_graduated", student_id=student.id)

    def publish_student_dropped(self, student):
        self._record("student_dropped", student_id=student.id)

    def publish_teacher_created(self, teacher):
        self._record("teacher_created", teacher_id=teacher.id)

    def publish_teacher_status_changed(self, teacher):
        self._record("teacher_status_changed",
                     teacher_id=teacher.id,
                     status=teacher.status.value)

    def publish_teacher_assigned_to_cohort(self, teacher_id, cohort_id):
        self._record("teacher_assigned_to_cohort",
                     teacher_id=teacher_id, cohort_id=cohort_id)

    def publish_teacher_unassigned_from_cohort(self, teacher_id, cohort_id):
        self._record("teacher_unassigned_from_cohort",
                     teacher_id=teacher_id, cohort_id=cohort_id)

    def publish_cohort_created(self, cohort):
        self._record("cohort_created", cohort_id=cohort.id)

    def publish_cohort_updated(self, cohort):
        self._record("cohort_updated", cohort_id=cohort.id)

    def publish_cohort_archived(self, cohort):
        self._record("cohort_archived", cohort_id=cohort.id)

    def publish_problem_solved(
        self, student_id, problem_id, attempts, solve_time_minutes
    ):
        self._record("problem_solved",
                     student_id=student_id,
                     problem_id=problem_id,
                     attempts=attempts,
                     solve_time_minutes=solve_time_minutes)

    def publish_attendance_updated(self, student_id, session_id, status):
        self._record("attendance_updated",
                     student_id=student_id,
                     session_id=session_id,
                     status=status)

    def publish_contest_finished(self, contest_id, cohort_id, results):
        self._record("contest_finished",
                     contest_id=contest_id,
                     cohort_id=cohort_id,
                     result_count=len(results))

    def publish_warning_issued(self, warning):
        self._record("warning_issued", warning_id=warning.id)

    def publish_warning_resolved(self, warning):
        self._record("warning_resolved", warning_id=warning.id)


class FakeWarningRulesRepository(WarningRulesRepositoryPort):

    def __init__(self):
        self._rules = WarningRules(
            min_attendance_percentage=60.0,
            min_contest_participation_percentage=50.0,
            max_warnings_before_escalation=3,
        )

    def get_rules(self) -> WarningRules:
        return self._rules

    def save_rules(self, rules: WarningRules) -> WarningRules:
        self._rules = rules
        return self._rules