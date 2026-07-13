import pytest
from uuid import uuid4
from datetime import datetime, timezone, date

from domain.enums import (
    StudentStatus, YearPhase, WarningStatus, WarningType,
)
from domain.exceptions import (
    StudentNotFoundError,
    WarningNotFoundError,
    WarningAlreadyDismissedError,
)
from domain.models import Student, Warning
from application.use_cases.warning.get_student_warnings import (
    GetStudentWarningsUseCase, GetStudentWarningsCommand,
)
from application.use_cases.warning.dismiss_warning import (
    DismissWarningUseCase, DismissWarningCommand,
)
from application.use_cases.warning.list_escalated_warnings import (
    ListEscalatedWarningsUseCase, ListEscalatedWarningsCommand,
)
from application.use_cases.warning.get_warning_rules import (
    GetWarningRulesUseCase,
)
from application.use_cases.warning.update_warning_rules import (
    UpdateWarningRulesUseCase, UpdateWarningRulesCommand,
)
from tests.fakes import (
    FakeStudentRepository,
    FakeWarningRepository,
    FakeEventPublisher,
    FakeWarningRulesRepository,
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


def make_warning(
    repo: FakeWarningRepository,
    student_id,
    **overrides,
) -> Warning:
    defaults = {
        "id": uuid4(),
        "student_id": student_id,
        "type": WarningType.LOW_ATTENDANCE,
        "status": WarningStatus.ACTIVE,
        "warning_number": 1,
        "issued_at": datetime.now(timezone.utc),
        "dismissed_at": None,
        "dismissed_by": None,
        "dismissal_note": None,
    }
    defaults.update(overrides)
    warning = Warning(**defaults)
    repo.save(warning)
    return warning


# ── GetStudentWarnings Tests ──────────────────────────────────────────────

class TestGetStudentWarnings:

    def test_returns_warnings_for_student(self):
        """Returns all warnings for a student."""
        student_repo = FakeStudentRepository()
        warning_repo = FakeWarningRepository()
        student = make_student(student_repo)
        make_warning(warning_repo, student.id)
        make_warning(warning_repo, student.id)
        use_case = GetStudentWarningsUseCase(
            student_repository=student_repo,
            warning_repository=warning_repo,
        )

        result = use_case.execute(
            GetStudentWarningsCommand(student_id=student.id)
        )

        assert len(result.warnings) == 2

    def test_returns_correct_active_warning_count(self):
        """Active warning count is correct."""
        student_repo = FakeStudentRepository()
        warning_repo = FakeWarningRepository()
        student = make_student(student_repo)
        make_warning(warning_repo, student.id, status=WarningStatus.ACTIVE)
        make_warning(warning_repo, student.id, status=WarningStatus.ACTIVE)
        make_warning(
            warning_repo, student.id, status=WarningStatus.DISMISSED
        )
        use_case = GetStudentWarningsUseCase(
            student_repository=student_repo,
            warning_repository=warning_repo,
        )

        result = use_case.execute(
            GetStudentWarningsCommand(student_id=student.id)
        )

        assert result.active_warning_count == 2

    def test_nonexistent_student_raises_error(self):
        """Fetching warnings for nonexistent student raises error."""
        use_case = GetStudentWarningsUseCase(
            student_repository=FakeStudentRepository(),
            warning_repository=FakeWarningRepository(),
        )

        with pytest.raises(StudentNotFoundError):
            use_case.execute(
                GetStudentWarningsCommand(student_id=uuid4())
            )


# ── DismissWarning Tests ──────────────────────────────────────────────────

class TestDismissWarning:

    def test_dismisses_active_warning(self):
        """Active warning is dismissed successfully."""
        student_repo = FakeStudentRepository()
        warning_repo = FakeWarningRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(student_repo)
        warning = make_warning(
            warning_repo, student.id, status=WarningStatus.ACTIVE
        )
        admin_id = uuid4()
        use_case = DismissWarningUseCase(
            warning_repository=warning_repo,
            event_publisher=event_publisher,
        )

        result = use_case.execute(DismissWarningCommand(
            warning_id=warning.id,
            dismissed_by=admin_id,
            note="Student showed improvement",
        ))

        assert result.status == WarningStatus.DISMISSED
        assert result.dismissed_by == admin_id
        assert result.dismissal_note == "Student showed improvement"

    def test_dismissed_at_is_set(self):
        """dismissed_at timestamp is set on dismissal."""
        warning_repo = FakeWarningRepository()
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        warning = make_warning(warning_repo, student.id)
        use_case = DismissWarningUseCase(
            warning_repository=warning_repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(DismissWarningCommand(
            warning_id=warning.id,
            dismissed_by=uuid4(),
            note="Improved",
        ))

        assert result.dismissed_at is not None

    def test_publishes_warning_resolved_event(self):
        """WarningResolved event is published on dismissal."""
        warning_repo = FakeWarningRepository()
        student_repo = FakeStudentRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(student_repo)
        warning = make_warning(warning_repo, student.id)
        use_case = DismissWarningUseCase(
            warning_repository=warning_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(DismissWarningCommand(
            warning_id=warning.id,
            dismissed_by=uuid4(),
            note="Improved",
        ))

        events = event_publisher.get_events_of_type("warning_resolved")
        assert len(events) == 1

    def test_dismissing_already_dismissed_warning_raises_error(self):
        """Cannot dismiss an already dismissed warning."""
        warning_repo = FakeWarningRepository()
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        warning = make_warning(
            warning_repo, student.id, status=WarningStatus.DISMISSED
        )
        use_case = DismissWarningUseCase(
            warning_repository=warning_repo,
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(WarningAlreadyDismissedError):
            use_case.execute(DismissWarningCommand(
                warning_id=warning.id,
                dismissed_by=uuid4(),
                note="Trying to dismiss again",
            ))

    def test_nonexistent_warning_raises_error(self):
        """Dismissing nonexistent warning raises error."""
        use_case = DismissWarningUseCase(
            warning_repository=FakeWarningRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(WarningNotFoundError):
            use_case.execute(DismissWarningCommand(
                warning_id=uuid4(),
                dismissed_by=uuid4(),
                note="Note",
            ))


# ── ListEscalatedWarnings Tests ───────────────────────────────────────────

class TestListEscalatedWarnings:

    def test_returns_escalated_warnings(self):
        """Returns all escalated warnings."""
        warning_repo = FakeWarningRepository()
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        make_warning(
            warning_repo, student.id, status=WarningStatus.ESCALATED
        )
        make_warning(
            warning_repo, student.id, status=WarningStatus.ESCALATED
        )
        make_warning(
            warning_repo, student.id, status=WarningStatus.ACTIVE
        )
        use_case = ListEscalatedWarningsUseCase(
            warning_repository=warning_repo,
        )

        result = use_case.execute(ListEscalatedWarningsCommand())

        assert len(result) == 2
        assert all(w.status == WarningStatus.ESCALATED for w in result)

    def test_returns_empty_when_no_escalated_warnings(self):
        """Returns empty list when no escalated warnings exist."""
        warning_repo = FakeWarningRepository()
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        make_warning(warning_repo, student.id, status=WarningStatus.ACTIVE)
        use_case = ListEscalatedWarningsUseCase(
            warning_repository=warning_repo,
        )

        result = use_case.execute(ListEscalatedWarningsCommand())

        assert len(result) == 0


# ── GetWarningRules Tests ─────────────────────────────────────────────────

class TestGetWarningRules:

    def test_returns_default_rules(self):
        """Returns the current warning rules configuration."""
        rules_repo = FakeWarningRulesRepository()
        use_case = GetWarningRulesUseCase(
            warning_rules_repository=rules_repo,
        )

        result = use_case.execute()

        assert result.min_attendance_percentage == 60.0
        assert result.min_contest_participation_percentage == 50.0
        assert result.max_warnings_before_escalation == 3


# ── UpdateWarningRules Tests ──────────────────────────────────────────────

class TestUpdateWarningRules:

    def test_updates_attendance_threshold(self):
        """Attendance threshold can be updated."""
        rules_repo = FakeWarningRulesRepository()
        use_case = UpdateWarningRulesUseCase(
            warning_rules_repository=rules_repo,
        )

        result = use_case.execute(UpdateWarningRulesCommand(
            min_attendance_percentage=70.0,
        ))

        assert result.min_attendance_percentage == 70.0

    def test_updates_contest_threshold(self):
        """Contest participation threshold can be updated."""
        rules_repo = FakeWarningRulesRepository()
        use_case = UpdateWarningRulesUseCase(
            warning_rules_repository=rules_repo,
        )

        result = use_case.execute(UpdateWarningRulesCommand(
            min_contest_participation_percentage=60.0,
        ))

        assert result.min_contest_participation_percentage == 60.0

    def test_updates_max_warnings(self):
        """Max warnings before escalation can be updated."""
        rules_repo = FakeWarningRulesRepository()
        use_case = UpdateWarningRulesUseCase(
            warning_rules_repository=rules_repo,
        )

        result = use_case.execute(UpdateWarningRulesCommand(
            max_warnings_before_escalation=2,
        ))

        assert result.max_warnings_before_escalation == 2

    def test_unspecified_fields_remain_unchanged(self):
        """Fields not in command keep their existing values."""
        rules_repo = FakeWarningRulesRepository()
        use_case = UpdateWarningRulesUseCase(
            warning_rules_repository=rules_repo,
        )

        # Only update attendance threshold
        result = use_case.execute(UpdateWarningRulesCommand(
            min_attendance_percentage=75.0,
        ))

        # Other fields should remain at defaults
        assert result.min_contest_participation_percentage == 50.0
        assert result.max_warnings_before_escalation == 3