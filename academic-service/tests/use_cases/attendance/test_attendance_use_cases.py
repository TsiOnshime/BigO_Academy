import pytest
from uuid import uuid4
from datetime import date

from domain.enums import (
    StudentStatus, YearPhase, CohortStatus, AttendanceStatus,
)
from domain.exceptions import (
    CohortNotFoundError, SessionNotFoundError, StudentNotFoundError,
)
from domain.models import Cohort, Student, ClassSession, AttendanceRecord
from application.use_cases.attendance.submit_attendance import (
    SubmitAttendanceUseCase, SubmitAttendanceCommand, AttendanceRecordInput,
)
from application.use_cases.attendance.get_session_attendance import (
    GetSessionAttendanceUseCase, GetSessionAttendanceCommand,
)
from application.use_cases.attendance.edit_attendance import (
    EditAttendanceUseCase, EditAttendanceCommand, AttendanceEditInput,
)
from application.use_cases.attendance.get_student_attendance import (
    GetStudentAttendanceUseCase, GetStudentAttendanceCommand,
)
from application.use_cases.attendance.get_cohort_attendance import (
    GetCohortAttendanceUseCase, GetCohortAttendanceCommand,
)
from tests.fakes import (
    FakeAttendanceRepository,
    FakeCohortRepository,
    FakeStudentRepository,
    FakeEventPublisher,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def make_cohort(repo: FakeCohortRepository, **overrides) -> Cohort:
    defaults = {
        "id": uuid4(),
        "name": "Batch 2024",
        "status": CohortStatus.ACTIVE,
        "intake_window_one": None,
        "intake_window_two": None,
        "start_date": date(2024, 1, 1),
        "expected_graduation_date": date(2026, 1, 1),
        "student_capacity": 50,
        "enrolled_student_count": 0,
        "teacher_count": 0,
    }
    defaults.update(overrides)
    cohort = Cohort(**defaults)
    repo.save(cohort)
    return cohort


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


def make_session(
    attendance_repo: FakeAttendanceRepository,
    cohort_id,
    student_ids: list,
    **overrides,
) -> ClassSession:
    records = [
        AttendanceRecord(
            student_id=sid,
            status=AttendanceStatus.PRESENT,
            note=None,
        )
        for sid in student_ids
    ]
    defaults = {
        "id": uuid4(),
        "cohort_id": cohort_id,
        "session_date": date.today(),
        "total_students": len(student_ids),
        "present_count": len(student_ids),
        "absent_count": 0,
        "excused_count": 0,
        "records": records,
    }
    defaults.update(overrides)
    session = ClassSession(**defaults)
    attendance_repo.save_session(session)
    return session


# ── SubmitAttendance Tests ────────────────────────────────────────────────

class TestSubmitAttendance:

    def test_submits_attendance_successfully(self):
        """Happy path — attendance session is created."""
        cohort_repo = FakeCohortRepository()
        attendance_repo = FakeAttendanceRepository()
        cohort = make_cohort(cohort_repo)
        student_id = uuid4()
        use_case = SubmitAttendanceUseCase(
            attendance_repository=attendance_repo,
            cohort_repository=cohort_repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(SubmitAttendanceCommand(
            cohort_id=cohort.id,
            session_date=date.today(),
            records=[
                AttendanceRecordInput(
                    student_id=student_id,
                    status=AttendanceStatus.PRESENT,
                ),
            ],
        ))

        assert result.cohort_id == cohort.id
        assert result.total_students == 1
        assert result.present_count == 1

    def test_counts_are_calculated_correctly(self):
        """Present, absent, excused counts are correct."""
        cohort_repo = FakeCohortRepository()
        attendance_repo = FakeAttendanceRepository()
        cohort = make_cohort(cohort_repo)
        use_case = SubmitAttendanceUseCase(
            attendance_repository=attendance_repo,
            cohort_repository=cohort_repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(SubmitAttendanceCommand(
            cohort_id=cohort.id,
            session_date=date.today(),
            records=[
                AttendanceRecordInput(
                    student_id=uuid4(),
                    status=AttendanceStatus.PRESENT,
                ),
                AttendanceRecordInput(
                    student_id=uuid4(),
                    status=AttendanceStatus.ABSENT,
                ),
                AttendanceRecordInput(
                    student_id=uuid4(),
                    status=AttendanceStatus.EXCUSED,
                ),
            ],
        ))

        assert result.present_count == 1
        assert result.absent_count == 1
        assert result.excused_count == 1

    def test_publishes_attendance_updated_event_per_student(self):
        """One AttendanceUpdated event per student record."""
        cohort_repo = FakeCohortRepository()
        attendance_repo = FakeAttendanceRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(cohort_repo)
        use_case = SubmitAttendanceUseCase(
            attendance_repository=attendance_repo,
            cohort_repository=cohort_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(SubmitAttendanceCommand(
            cohort_id=cohort.id,
            session_date=date.today(),
            records=[
                AttendanceRecordInput(
                    student_id=uuid4(),
                    status=AttendanceStatus.PRESENT,
                ),
                AttendanceRecordInput(
                    student_id=uuid4(),
                    status=AttendanceStatus.PRESENT,
                ),
            ],
        ))

        events = event_publisher.get_events_of_type("attendance_updated")
        assert len(events) == 2

    def test_nonexistent_cohort_raises_error(self):
        """Submitting attendance for nonexistent cohort raises error."""
        use_case = SubmitAttendanceUseCase(
            attendance_repository=FakeAttendanceRepository(),
            cohort_repository=FakeCohortRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(SubmitAttendanceCommand(
                cohort_id=uuid4(),
                session_date=date.today(),
                records=[],
            ))


# ── GetSessionAttendance Tests ────────────────────────────────────────────

class TestGetSessionAttendance:

    def test_returns_existing_session(self):
        """Fetching an existing session returns it with records."""
        attendance_repo = FakeAttendanceRepository()
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        student_id = uuid4()
        session = make_session(attendance_repo, cohort.id, [student_id])
        use_case = GetSessionAttendanceUseCase(
            attendance_repository=attendance_repo,
        )

        result = use_case.execute(
            GetSessionAttendanceCommand(session_id=session.id)
        )

        assert result.id == session.id
        assert len(result.records) == 1

    def test_nonexistent_session_raises_error(self):
        """Fetching nonexistent session raises SessionNotFoundError."""
        use_case = GetSessionAttendanceUseCase(
            attendance_repository=FakeAttendanceRepository(),
        )

        with pytest.raises(SessionNotFoundError):
            use_case.execute(
                GetSessionAttendanceCommand(session_id=uuid4())
            )


# ── EditAttendance Tests ──────────────────────────────────────────────────

class TestEditAttendance:

    def test_edits_attendance_record(self):
        """Attendance status can be changed after submission."""
        attendance_repo = FakeAttendanceRepository()
        cohort_repo = FakeCohortRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(cohort_repo)
        student_id = uuid4()
        session = make_session(attendance_repo, cohort.id, [student_id])
        use_case = EditAttendanceUseCase(
            attendance_repository=attendance_repo,
            event_publisher=event_publisher,
        )

        result = use_case.execute(EditAttendanceCommand(
            session_id=session.id,
            records=[
                AttendanceEditInput(
                    student_id=student_id,
                    status=AttendanceStatus.ABSENT,
                ),
            ],
        ))

        updated_record = next(
            r for r in result.records if r.student_id == student_id
        )
        assert updated_record.status == AttendanceStatus.ABSENT

    def test_recalculates_counts_after_edit(self):
        """Counts are recalculated after editing records."""
        attendance_repo = FakeAttendanceRepository()
        event_publisher = FakeEventPublisher()
        cohort_id = uuid4()
        student_id = uuid4()
        session = make_session(
            attendance_repo, cohort_id, [student_id]
        )
        # Initially present_count = 1
        use_case = EditAttendanceUseCase(
            attendance_repository=attendance_repo,
            event_publisher=event_publisher,
        )

        result = use_case.execute(EditAttendanceCommand(
            session_id=session.id,
            records=[
                AttendanceEditInput(
                    student_id=student_id,
                    status=AttendanceStatus.ABSENT,
                ),
            ],
        ))

        assert result.present_count == 0
        assert result.absent_count == 1

    def test_publishes_attendance_updated_event(self):
        """AttendanceUpdated event published for edited records."""
        attendance_repo = FakeAttendanceRepository()
        event_publisher = FakeEventPublisher()
        cohort_id = uuid4()
        student_id = uuid4()
        session = make_session(attendance_repo, cohort_id, [student_id])
        use_case = EditAttendanceUseCase(
            attendance_repository=attendance_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(EditAttendanceCommand(
            session_id=session.id,
            records=[
                AttendanceEditInput(
                    student_id=student_id,
                    status=AttendanceStatus.ABSENT,
                ),
            ],
        ))

        events = event_publisher.get_events_of_type("attendance_updated")
        assert len(events) == 1

    def test_nonexistent_session_raises_error(self):
        """Editing nonexistent session raises error."""
        use_case = EditAttendanceUseCase(
            attendance_repository=FakeAttendanceRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(SessionNotFoundError):
            use_case.execute(EditAttendanceCommand(
                session_id=uuid4(),
                records=[],
            ))


# ── GetStudentAttendance Tests ────────────────────────────────────────────

class TestGetStudentAttendance:

    def test_returns_student_attendance_history(self):
        """Returns attendance history for a student."""
        student_repo = FakeStudentRepository()
        attendance_repo = FakeAttendanceRepository()
        student = make_student(student_repo)
        cohort_id = uuid4()
        make_session(attendance_repo, cohort_id, [student.id])
        make_session(attendance_repo, cohort_id, [student.id])
        use_case = GetStudentAttendanceUseCase(
            student_repository=student_repo,
            attendance_repository=attendance_repo,
        )

        result = use_case.execute(
            GetStudentAttendanceCommand(student_id=student.id)
        )

        assert result.total_sessions == 2
        assert result.present_count == 2

    def test_calculates_attendance_percentage(self):
        """Attendance percentage is calculated correctly."""
        student_repo = FakeStudentRepository()
        attendance_repo = FakeAttendanceRepository()
        student = make_student(student_repo)
        cohort_id = uuid4()

        # 2 present sessions
        make_session(attendance_repo, cohort_id, [student.id])
        make_session(attendance_repo, cohort_id, [student.id])

        # 1 absent session
        absent_session = make_session(
            attendance_repo, cohort_id, [],
        )
        absent_session.records = [
            AttendanceRecord(
                student_id=student.id,
                status=AttendanceStatus.ABSENT,
                note=None,
            )
        ]
        attendance_repo.save_session(absent_session)

        use_case = GetStudentAttendanceUseCase(
            student_repository=student_repo,
            attendance_repository=attendance_repo,
        )

        result = use_case.execute(
            GetStudentAttendanceCommand(student_id=student.id)
        )

        assert result.attendance_percentage == pytest.approx(66.67, rel=0.01)

    def test_nonexistent_student_raises_error(self):
        """Fetching attendance for nonexistent student raises error."""
        use_case = GetStudentAttendanceUseCase(
            student_repository=FakeStudentRepository(),
            attendance_repository=FakeAttendanceRepository(),
        )

        with pytest.raises(StudentNotFoundError):
            use_case.execute(
                GetStudentAttendanceCommand(student_id=uuid4())
            )


# ── GetCohortAttendance Tests ─────────────────────────────────────────────

class TestGetCohortAttendance:

    def test_returns_sessions_for_cohort(self):
        """Returns all sessions for a cohort."""
        cohort_repo = FakeCohortRepository()
        attendance_repo = FakeAttendanceRepository()
        cohort = make_cohort(cohort_repo)
        make_session(attendance_repo, cohort.id, [uuid4()])
        make_session(attendance_repo, cohort.id, [uuid4()])
        make_session(attendance_repo, uuid4(), [uuid4()])  # other cohort
        use_case = GetCohortAttendanceUseCase(
            cohort_repository=cohort_repo,
            attendance_repository=attendance_repo,
        )

        result = use_case.execute(
            GetCohortAttendanceCommand(cohort_id=cohort.id)
        )

        assert len(result) == 2

    def test_nonexistent_cohort_raises_error(self):
        """Fetching attendance for nonexistent cohort raises error."""
        use_case = GetCohortAttendanceUseCase(
            cohort_repository=FakeCohortRepository(),
            attendance_repository=FakeAttendanceRepository(),
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(
                GetCohortAttendanceCommand(cohort_id=uuid4())
            )