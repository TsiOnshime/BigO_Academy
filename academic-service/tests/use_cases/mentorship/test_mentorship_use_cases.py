import pytest
from uuid import uuid4
from datetime import datetime, timezone, date

from domain.enums import (
    StudentStatus, TeacherStatus, YearPhase,
    MentorshipSessionStatus,
)
from domain.exceptions import (
    StudentNotFoundError,
    TeacherNotFoundError,
    MentorshipSessionNotFoundError,
)
from domain.models import Student, Teacher, MentorshipSession
from application.use_cases.mentorship.schedule_mentorship import (
    ScheduleMentorshipUseCase, ScheduleMentorshipCommand,
)
from application.use_cases.mentorship.list_mentorship_sessions import (
    ListMentorshipSessionsUseCase, ListMentorshipSessionsCommand,
)
from application.use_cases.mentorship.get_mentorship_session import (
    GetMentorshipSessionUseCase, GetMentorshipSessionCommand,
)
from application.use_cases.mentorship.update_mentorship_session import (
    UpdateMentorshipSessionUseCase, UpdateMentorshipSessionCommand,
)
from tests.fakes import (
    FakeMentorshipRepository,
    FakeStudentRepository,
    FakeTeacherRepository,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def make_student(repo: FakeStudentRepository, **overrides) -> Student:
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "full_name": "Abel Girma",
        "email": "abel@example.com",
        "cohort_id": uuid4(),
        "year_phase": YearPhase.YEAR_ONE,
        "status": StudentStatus.ACTIVE,
        "assigned_teacher_id": None,
        "attendance_percentage": 0.0,
        "active_warning_count": 0,
        "joined_at": date.today(),
    }
    defaults.update(overrides)
    student = Student(**defaults)
    repo.save(student)
    return student


def make_teacher(repo: FakeTeacherRepository, **overrides) -> Teacher:
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "full_name": "Meron Tadesse",
        "email": "meron@a2sv.org",
        "status": TeacherStatus.ACTIVE,
        "assigned_cohort_ids": [],
    }
    defaults.update(overrides)
    teacher = Teacher(**defaults)
    repo.save(teacher)
    return teacher


def make_session(
    repo: FakeMentorshipRepository,
    teacher_id,
    student_id,
    **overrides,
) -> MentorshipSession:
    defaults = {
        "id": uuid4(),
        "teacher_id": teacher_id,
        "student_id": student_id,
        "scheduled_at": datetime.now(timezone.utc),
        "status": MentorshipSessionStatus.SCHEDULED,
        "notes": None,
    }
    defaults.update(overrides)
    session = MentorshipSession(**defaults)
    repo.save(session)
    return session


# ── ScheduleMentorship Tests ──────────────────────────────────────────────

class TestScheduleMentorship:

    def test_schedules_session_successfully(self):
        """Happy path — valid input creates a mentorship session."""
        student_repo = FakeStudentRepository()
        teacher_repo = FakeTeacherRepository()
        mentorship_repo = FakeMentorshipRepository()
        student = make_student(student_repo)
        teacher = make_teacher(teacher_repo)
        use_case = ScheduleMentorshipUseCase(
            mentorship_repository=mentorship_repo,
            student_repository=student_repo,
            teacher_repository=teacher_repo,
        )

        result = use_case.execute(ScheduleMentorshipCommand(
            teacher_id=teacher.id,
            student_id=student.id,
            scheduled_at=datetime.now(timezone.utc),
        ))

        assert result.teacher_id == teacher.id
        assert result.student_id == student.id

    def test_new_session_starts_scheduled(self):
        """New mentorship sessions start with SCHEDULED status."""
        student_repo = FakeStudentRepository()
        teacher_repo = FakeTeacherRepository()
        mentorship_repo = FakeMentorshipRepository()
        student = make_student(student_repo)
        teacher = make_teacher(teacher_repo)
        use_case = ScheduleMentorshipUseCase(
            mentorship_repository=mentorship_repo,
            student_repository=student_repo,
            teacher_repository=teacher_repo,
        )

        result = use_case.execute(ScheduleMentorshipCommand(
            teacher_id=teacher.id,
            student_id=student.id,
            scheduled_at=datetime.now(timezone.utc),
        ))

        assert result.status == MentorshipSessionStatus.SCHEDULED

    def test_new_session_has_no_notes(self):
        """New sessions have no notes — added after completion."""
        student_repo = FakeStudentRepository()
        teacher_repo = FakeTeacherRepository()
        mentorship_repo = FakeMentorshipRepository()
        student = make_student(student_repo)
        teacher = make_teacher(teacher_repo)
        use_case = ScheduleMentorshipUseCase(
            mentorship_repository=mentorship_repo,
            student_repository=student_repo,
            teacher_repository=teacher_repo,
        )

        result = use_case.execute(ScheduleMentorshipCommand(
            teacher_id=teacher.id,
            student_id=student.id,
            scheduled_at=datetime.now(timezone.utc),
        ))

        assert result.notes is None

    def test_session_saved_to_repository(self):
        """Session is findable in repo after scheduling."""
        student_repo = FakeStudentRepository()
        teacher_repo = FakeTeacherRepository()
        mentorship_repo = FakeMentorshipRepository()
        student = make_student(student_repo)
        teacher = make_teacher(teacher_repo)
        use_case = ScheduleMentorshipUseCase(
            mentorship_repository=mentorship_repo,
            student_repository=student_repo,
            teacher_repository=teacher_repo,
        )

        result = use_case.execute(ScheduleMentorshipCommand(
            teacher_id=teacher.id,
            student_id=student.id,
            scheduled_at=datetime.now(timezone.utc),
        ))

        found = mentorship_repo.find_by_id(result.id)
        assert found is not None

    def test_nonexistent_teacher_raises_error(self):
        """Scheduling with nonexistent teacher raises error."""
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        use_case = ScheduleMentorshipUseCase(
            mentorship_repository=FakeMentorshipRepository(),
            student_repository=student_repo,
            teacher_repository=FakeTeacherRepository(),
        )

        with pytest.raises(TeacherNotFoundError):
            use_case.execute(ScheduleMentorshipCommand(
                teacher_id=uuid4(),
                student_id=student.id,
                scheduled_at=datetime.now(timezone.utc),
            ))

    def test_nonexistent_student_raises_error(self):
        """Scheduling with nonexistent student raises error."""
        teacher_repo = FakeTeacherRepository()
        teacher = make_teacher(teacher_repo)
        use_case = ScheduleMentorshipUseCase(
            mentorship_repository=FakeMentorshipRepository(),
            student_repository=FakeStudentRepository(),
            teacher_repository=teacher_repo,
        )

        with pytest.raises(StudentNotFoundError):
            use_case.execute(ScheduleMentorshipCommand(
                teacher_id=teacher.id,
                student_id=uuid4(),
                scheduled_at=datetime.now(timezone.utc),
            ))


# ── ListMentorshipSessions Tests ──────────────────────────────────────────

class TestListMentorshipSessions:

    def test_returns_sessions_for_student(self):
        """Returns all sessions for a specific student."""
        mentorship_repo = FakeMentorshipRepository()
        teacher_id = uuid4()
        student_id = uuid4()
        other_student_id = uuid4()
        make_session(mentorship_repo, teacher_id, student_id)
        make_session(mentorship_repo, teacher_id, student_id)
        make_session(mentorship_repo, teacher_id, other_student_id)
        use_case = ListMentorshipSessionsUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(
            ListMentorshipSessionsCommand(student_id=student_id)
        )

        assert len(result) == 2
        assert all(s.student_id == student_id for s in result)

    def test_returns_sessions_for_teacher(self):
        """Returns all sessions for a specific teacher."""
        mentorship_repo = FakeMentorshipRepository()
        teacher_id = uuid4()
        other_teacher_id = uuid4()
        student_id = uuid4()
        make_session(mentorship_repo, teacher_id, student_id)
        make_session(mentorship_repo, teacher_id, student_id)
        make_session(mentorship_repo, other_teacher_id, student_id)
        use_case = ListMentorshipSessionsUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(
            ListMentorshipSessionsCommand(teacher_id=teacher_id)
        )

        assert len(result) == 2
        assert all(s.teacher_id == teacher_id for s in result)

    def test_returns_empty_when_no_filter(self):
        """Returns empty list when no student or teacher filter provided."""
        mentorship_repo = FakeMentorshipRepository()
        make_session(mentorship_repo, uuid4(), uuid4())
        use_case = ListMentorshipSessionsUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(ListMentorshipSessionsCommand())

        assert len(result) == 0


# ── GetMentorshipSession Tests ────────────────────────────────────────────

class TestGetMentorshipSession:

    def test_returns_existing_session(self):
        """Fetching an existing session returns it."""
        mentorship_repo = FakeMentorshipRepository()
        session = make_session(mentorship_repo, uuid4(), uuid4())
        use_case = GetMentorshipSessionUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(
            GetMentorshipSessionCommand(session_id=session.id)
        )

        assert result.id == session.id

    def test_nonexistent_session_raises_error(self):
        """Fetching nonexistent session raises error."""
        use_case = GetMentorshipSessionUseCase(
            mentorship_repository=FakeMentorshipRepository(),
        )

        with pytest.raises(MentorshipSessionNotFoundError):
            use_case.execute(
                GetMentorshipSessionCommand(session_id=uuid4())
            )


# ── UpdateMentorshipSession Tests ─────────────────────────────────────────

class TestUpdateMentorshipSession:

    def test_updates_status_to_completed(self):
        """Session status can be updated to COMPLETED."""
        mentorship_repo = FakeMentorshipRepository()
        session = make_session(
            mentorship_repo, uuid4(), uuid4(),
            status=MentorshipSessionStatus.SCHEDULED,
        )
        use_case = UpdateMentorshipSessionUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(UpdateMentorshipSessionCommand(
            session_id=session.id,
            status=MentorshipSessionStatus.COMPLETED,
        ))

        assert result.status == MentorshipSessionStatus.COMPLETED

    def test_adds_notes_after_completion(self):
        """Teacher can add notes to a session."""
        mentorship_repo = FakeMentorshipRepository()
        session = make_session(mentorship_repo, uuid4(), uuid4(), notes=None)
        use_case = UpdateMentorshipSessionUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(UpdateMentorshipSessionCommand(
            session_id=session.id,
            notes="Student needs to focus on dynamic programming.",
        ))

        assert result.notes == "Student needs to focus on dynamic programming."

    def test_cancels_scheduled_session(self):
        """A scheduled session can be cancelled."""
        mentorship_repo = FakeMentorshipRepository()
        session = make_session(
            mentorship_repo, uuid4(), uuid4(),
            status=MentorshipSessionStatus.SCHEDULED,
        )
        use_case = UpdateMentorshipSessionUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(UpdateMentorshipSessionCommand(
            session_id=session.id,
            status=MentorshipSessionStatus.CANCELLED,
        ))

        assert result.status == MentorshipSessionStatus.CANCELLED

    def test_updates_scheduled_time(self):
        """Session scheduled time can be rescheduled."""
        mentorship_repo = FakeMentorshipRepository()
        session = make_session(mentorship_repo, uuid4(), uuid4())
        new_time = datetime(2025, 12, 1, 10, 0, 0, tzinfo=timezone.utc)
        use_case = UpdateMentorshipSessionUseCase(
            mentorship_repository=mentorship_repo,
        )

        result = use_case.execute(UpdateMentorshipSessionCommand(
            session_id=session.id,
            scheduled_at=new_time,
        ))

        assert result.scheduled_at == new_time

    def test_nonexistent_session_raises_error(self):
        """Updating nonexistent session raises error."""
        use_case = UpdateMentorshipSessionUseCase(
            mentorship_repository=FakeMentorshipRepository(),
        )

        with pytest.raises(MentorshipSessionNotFoundError):
            use_case.execute(UpdateMentorshipSessionCommand(
                session_id=uuid4(),
                status=MentorshipSessionStatus.COMPLETED,
            ))