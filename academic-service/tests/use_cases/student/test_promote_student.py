import pytest
from datetime import date
from uuid import uuid4

from domain.enums import StudentStatus, YearPhase
from domain.exceptions import StudentNotFoundError, StudentNotEligibleForPromotionError
from domain.models import Student
from application.use_cases.student.promote_student import (
    PromoteStudentUseCase,
    PromoteStudentCommand,
)
from tests.fakes import FakeStudentRepository, FakeEventPublisher


def make_student(repo, **overrides) -> Student:
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


def make_use_case(repo=None, event_publisher=None):
    return PromoteStudentUseCase(
        student_repository=repo or FakeStudentRepository(),
        event_publisher=event_publisher or FakeEventPublisher(),
    )


class TestPromoteStudent:

    def test_promotes_eligible_student_to_year_two(self):
        """Year 1 ACTIVE student gets promoted to Year 2."""
        repo = FakeStudentRepository()
        student = make_student(
            repo,
            year_phase=YearPhase.YEAR_ONE,
            status=StudentStatus.ACTIVE,
        )
        use_case = make_use_case(repo=repo)

        result = use_case.execute(PromoteStudentCommand(student_id=student.id))

        assert result.year_phase == YearPhase.YEAR_TWO

    def test_publishes_student_promoted_event(self):
        """Promotion publishes StudentPromoted event."""
        repo = FakeStudentRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(repo)
        use_case = make_use_case(repo=repo, event_publisher=event_publisher)

        use_case.execute(PromoteStudentCommand(student_id=student.id))

        events = event_publisher.get_events_of_type("student_promoted")
        assert len(events) == 1

    def test_year_two_student_cannot_be_promoted(self):
        """A student already in Year 2 cannot be promoted again."""
        repo = FakeStudentRepository()
        student = make_student(repo, year_phase=YearPhase.YEAR_TWO)
        use_case = make_use_case(repo=repo)

        with pytest.raises(StudentNotEligibleForPromotionError):
            use_case.execute(PromoteStudentCommand(student_id=student.id))

    def test_probation_student_cannot_be_promoted(self):
        """A student on probation is not eligible for promotion."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.PROBATION)
        use_case = make_use_case(repo=repo)

        with pytest.raises(StudentNotEligibleForPromotionError):
            use_case.execute(PromoteStudentCommand(student_id=student.id))

    def test_dropped_student_cannot_be_promoted(self):
        """A dropped student cannot be promoted."""
        repo = FakeStudentRepository()
        student = make_student(repo, status=StudentStatus.DROPPED)
        use_case = make_use_case(repo=repo)

        with pytest.raises(StudentNotEligibleForPromotionError):
            use_case.execute(PromoteStudentCommand(student_id=student.id))

    def test_nonexistent_student_raises_error(self):
        """Promoting a nonexistent student raises error."""
        use_case = make_use_case()

        with pytest.raises(StudentNotFoundError):
            use_case.execute(PromoteStudentCommand(student_id=uuid4()))