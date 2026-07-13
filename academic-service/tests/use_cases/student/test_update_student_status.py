import pytest
from datetime import date
from uuid import uuid4

from domain.enums import StudentStatus, YearPhase, CohortStatus
from domain.exceptions import (
    StudentNotFoundError,
    InvalidStudentStatusTransitionError,
)
from domain.models import Student
from application.use_cases.student.update_student_status import (
    UpdateStudentStatusUseCase,
    UpdateStudentStatusCommand,
)
from tests.fakes import FakeStudentRepository, FakeEventPublisher


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


def make_use_case(student_repo=None, event_publisher=None):
    return UpdateStudentStatusUseCase(
        student_repository=student_repo or FakeStudentRepository(),
        event_publisher=event_publisher or FakeEventPublisher(),
    )


# ── Tests ─────────────────────────────────────────────────────────────────

class TestUpdateStudentStatus:

    def test_active_to_probation_succeeds(self):
        """ACTIVE → PROBATION is a valid transition."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.ACTIVE)
        use_case = make_use_case(student_repo=repo)

        result = use_case.execute(UpdateStudentStatusCommand(
            student_id=student.id,
            new_status=StudentStatus.PROBATION,
        ))

        assert result.status == StudentStatus.PROBATION

    def test_probation_to_dropped_succeeds(self):
        """PROBATION → DROPPED is a valid transition."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.PROBATION)
        use_case = make_use_case(student_repo=repo)

        result = use_case.execute(UpdateStudentStatusCommand(
            student_id=student.id,
            new_status=StudentStatus.DROPPED,
        ))

        assert result.status == StudentStatus.DROPPED

    def test_probation_to_active_succeeds(self):
        """PROBATION → ACTIVE is valid — student improved."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.PROBATION)
        use_case = make_use_case(student_repo=repo)

        result = use_case.execute(UpdateStudentStatusCommand(
            student_id=student.id,
            new_status=StudentStatus.ACTIVE,
        ))

        assert result.status == StudentStatus.ACTIVE

    def test_any_status_to_archived_succeeds(self):
        """Any status → ARCHIVED is always valid."""
        repo = FakeStudentRepository()
        use_case = make_use_case(student_repo=repo)

        for status in [
            StudentStatus.ACTIVE,
            StudentStatus.PROBATION,
            StudentStatus.DROPPED,
            StudentStatus.GRADUATED,
        ]:
            student = make_student(repo, status=status)
            result = use_case.execute(UpdateStudentStatusCommand(
                student_id=student.id,
                new_status=StudentStatus.ARCHIVED,
            ))
            assert result.status == StudentStatus.ARCHIVED

    def test_active_to_dropped_is_invalid(self):
        """ACTIVE → DROPPED is not a valid transition."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.ACTIVE)
        use_case = make_use_case(student_repo=repo)

        with pytest.raises(InvalidStudentStatusTransitionError):
            use_case.execute(UpdateStudentStatusCommand(
                student_id=student.id,
                new_status=StudentStatus.DROPPED,
            ))

    def test_dropped_to_active_is_invalid(self):
        """DROPPED → ACTIVE is not valid — once dropped, cannot return."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.DROPPED)
        use_case = make_use_case(student_repo=repo)

        with pytest.raises(InvalidStudentStatusTransitionError):
            use_case.execute(UpdateStudentStatusCommand(
                student_id=student.id,
                new_status=StudentStatus.ACTIVE,
            ))

    def test_graduated_to_active_is_invalid(self):
        """GRADUATED → ACTIVE is not valid."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.GRADUATED)
        use_case = make_use_case(student_repo=repo)

        with pytest.raises(InvalidStudentStatusTransitionError):
            use_case.execute(UpdateStudentStatusCommand(
                student_id=student.id,
                new_status=StudentStatus.ACTIVE,
            ))

    def test_dropped_publishes_student_dropped_event(self):
        """Dropping a student publishes StudentDropped event."""
        repo = FakeStudentRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(repo, status=StudentStatus.PROBATION)
        use_case = make_use_case(
            student_repo=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(UpdateStudentStatusCommand(
            student_id=student.id,
            new_status=StudentStatus.DROPPED,
        ))

        events = event_publisher.get_events_of_type("student_dropped")
        assert len(events) == 1

    def test_graduated_publishes_student_graduated_event(self):
        """Graduating a student publishes StudentGraduated event."""
        repo = FakeStudentRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(repo, status=StudentStatus.ACTIVE)
        use_case = make_use_case(
            student_repo=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(UpdateStudentStatusCommand(
            student_id=student.id,
            new_status=StudentStatus.GRADUATED,
        ))

        events = event_publisher.get_events_of_type("student_graduated")
        assert len(events) == 1

    def test_other_transitions_publish_status_changed_event(self):
        """Non-special transitions publish StudentStatusChanged event."""
        repo = FakeStudentRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(repo, status=StudentStatus.ACTIVE)
        use_case = make_use_case(
            student_repo=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(UpdateStudentStatusCommand(
            student_id=student.id,
            new_status=StudentStatus.PROBATION,
        ))

        events = event_publisher.get_events_of_type("student_status_changed")
        assert len(events) == 1

    def test_nonexistent_student_raises_error(self):
        """Updating status of nonexistent student raises error."""
        use_case = make_use_case()

        with pytest.raises(StudentNotFoundError):
            use_case.execute(UpdateStudentStatusCommand(
                student_id=uuid4(),
                new_status=StudentStatus.PROBATION,
            ))