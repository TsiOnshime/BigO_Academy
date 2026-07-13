import pytest
from datetime import date
from uuid import uuid4

from domain.enums import StudentStatus, YearPhase, CohortStatus
from domain.exceptions import (
    StudentAlreadyExistsError,
    CohortNotFoundError,
    CohortArchivedError,
)
from domain.models import Cohort
from application.use_cases.student.create_student import (
    CreateStudentUseCase,
    CreateStudentCommand,
)
from tests.fakes import (
    FakeStudentRepository,
    FakeCohortRepository,
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


def make_use_case(student_repo=None, cohort_repo=None, event_publisher=None):
    return CreateStudentUseCase(
        student_repository=student_repo or FakeStudentRepository(),
        cohort_repository=cohort_repo or FakeCohortRepository(),
        event_publisher=event_publisher or FakeEventPublisher(),
    )


def make_command(cohort_id, **overrides):
    defaults = {
        "user_id": uuid4(),
        "full_name": "Abel Girma",
        "email": "abel@example.com",
        "cohort_id": cohort_id,
        "joined_at": date.today(),
    }
    defaults.update(overrides)
    return CreateStudentCommand(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────

class TestCreateStudent:

    def test_creates_student_successfully(self):
        """Happy path — valid input creates a student."""
        student_repo = FakeStudentRepository()
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(
            student_repo=student_repo,
            cohort_repo=cohort_repo,
        )

        result = use_case.execute(make_command(cohort.id))

        assert result.student is not None
        assert result.student.full_name == "Abel Girma"
        assert result.student.email == "abel@example.com"

    def test_new_student_starts_in_year_one(self):
        """All new students start in Year 1."""
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(cohort_repo=cohort_repo)

        result = use_case.execute(make_command(cohort.id))

        assert result.student.year_phase == YearPhase.YEAR_ONE

    def test_new_student_starts_active(self):
        """New students start with ACTIVE status."""
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(cohort_repo=cohort_repo)

        result = use_case.execute(make_command(cohort.id))

        assert result.student.status == StudentStatus.ACTIVE

    def test_new_student_has_zero_warnings(self):
        """New students have no warnings."""
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(cohort_repo=cohort_repo)

        result = use_case.execute(make_command(cohort.id))

        assert result.student.active_warning_count == 0

    def test_new_student_has_zero_attendance(self):
        """New students have 0% attendance — no sessions yet."""
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(cohort_repo=cohort_repo)

        result = use_case.execute(make_command(cohort.id))

        assert result.student.attendance_percentage == 0.0

    def test_student_saved_to_repository(self):
        """After creation, student must be findable in the repo."""
        student_repo = FakeStudentRepository()
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(
            student_repo=student_repo,
            cohort_repo=cohort_repo,
        )

        result = use_case.execute(make_command(cohort.id))

        found = student_repo.find_by_id(result.student.id)
        assert found is not None
        assert found.email == "abel@example.com"

    def test_student_assigned_to_cohort(self):
        """After creation, student must be assigned to the cohort."""
        student_repo = FakeStudentRepository()
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(
            student_repo=student_repo,
            cohort_repo=cohort_repo,
        )

        result = use_case.execute(make_command(cohort.id))

        assert cohort_repo.student_in_cohort(cohort.id, result.student.id)

    def test_cohort_enrolled_count_increases(self):
        """Cohort enrolled_student_count must increase by 1."""
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo, enrolled_student_count=0)
        use_case = make_use_case(cohort_repo=cohort_repo)

        use_case.execute(make_command(cohort.id))

        updated_cohort = cohort_repo.find_by_id(cohort.id)
        assert updated_cohort.enrolled_student_count == 1

    def test_publishes_student_created_event(self):
        """A StudentCreated event must be published after creation."""
        cohort_repo = FakeCohortRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(
            cohort_repo=cohort_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(make_command(cohort.id))

        events = event_publisher.get_events_of_type("student_created")
        assert len(events) == 1

    def test_duplicate_user_id_raises_error(self):
        """Creating a student profile for an existing user_id raises error."""
        student_repo = FakeStudentRepository()
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = make_use_case(
            student_repo=student_repo,
            cohort_repo=cohort_repo,
        )
        user_id = uuid4()

        # Create once
        use_case.execute(make_command(cohort.id, user_id=user_id))

        # Try again with same user_id
        with pytest.raises(StudentAlreadyExistsError):
            use_case.execute(make_command(cohort.id, user_id=user_id))

    def test_nonexistent_cohort_raises_error(self):
        """Assigning student to a non-existent cohort raises error."""
        use_case = make_use_case()

        with pytest.raises(CohortNotFoundError):
            use_case.execute(make_command(cohort_id=uuid4()))

    def test_archived_cohort_raises_error(self):
        """Cannot add students to an archived cohort."""
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo, status=CohortStatus.ARCHIVED)
        use_case = make_use_case(cohort_repo=cohort_repo)

        with pytest.raises(CohortArchivedError):
            use_case.execute(make_command(cohort.id))