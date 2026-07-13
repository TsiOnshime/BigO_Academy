import pytest
from datetime import date
from uuid import uuid4

from domain.enums import CohortStatus, StudentStatus, TeacherStatus, YearPhase
from domain.exceptions import (
    CohortNotFoundError,
    CohortArchivedError,
    StudentNotFoundError,
    TeacherNotFoundError,
    StudentAlreadyInCohortError,
    TeacherAlreadyInCohortError,
)
from domain.models import Cohort, Student, Teacher
from application.use_cases.cohort.create_cohort import (
    CreateCohortUseCase, CreateCohortCommand,
)
from application.use_cases.cohort.get_cohort import (
    GetCohortUseCase, GetCohortCommand,
)
from application.use_cases.cohort.list_cohorts import (
    ListCohortsUseCase, ListCohortsCommand,
)
from application.use_cases.cohort.update_cohort import (
    UpdateCohortUseCase, UpdateCohortCommand,
)
from application.use_cases.cohort.archive_cohort import (
    ArchiveCohortUseCase, ArchiveCohortCommand,
)
from application.use_cases.cohort.assign_student_to_cohort import (
    AssignStudentToCohortUseCase, AssignStudentToCohortCommand,
)
from application.use_cases.cohort.assign_teacher_to_cohort import (
    AssignTeacherToCohortUseCase, AssignTeacherToCohortCommand,
)
from application.use_cases.cohort.unassign_teacher_from_cohort import (
    UnassignTeacherFromCohortUseCase, UnassignTeacherFromCohortCommand,
)
from tests.fakes import (
    FakeCohortRepository,
    FakeStudentRepository,
    FakeTeacherRepository,
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
        "cohort_id": None,
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


# ── CreateCohort Tests ────────────────────────────────────────────────────

class TestCreateCohort:

    def test_creates_cohort_successfully(self):
        """Happy path — valid input creates a cohort."""
        repo = FakeCohortRepository()
        use_case = CreateCohortUseCase(
            cohort_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(CreateCohortCommand(
            name="Batch 2024",
            start_date=date(2024, 1, 1),
            expected_graduation_date=date(2026, 1, 1),
            student_capacity=50,
        ))

        assert result.cohort.name == "Batch 2024"
        assert result.cohort.status == CohortStatus.ACTIVE

    def test_new_cohort_starts_with_zero_students(self):
        """New cohort has no enrolled students."""
        repo = FakeCohortRepository()
        use_case = CreateCohortUseCase(
            cohort_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(CreateCohortCommand(
            name="Batch 2024",
            start_date=date(2024, 1, 1),
            expected_graduation_date=date(2026, 1, 1),
            student_capacity=50,
        ))

        assert result.cohort.enrolled_student_count == 0

    def test_publishes_cohort_created_event(self):
        """CohortCreated event must be published."""
        repo = FakeCohortRepository()
        event_publisher = FakeEventPublisher()
        use_case = CreateCohortUseCase(
            cohort_repository=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(CreateCohortCommand(
            name="Batch 2024",
            start_date=date(2024, 1, 1),
            expected_graduation_date=date(2026, 1, 1),
            student_capacity=50,
        ))

        events = event_publisher.get_events_of_type("cohort_created")
        assert len(events) == 1


# ── GetCohort Tests ───────────────────────────────────────────────────────

class TestGetCohort:

    def test_returns_existing_cohort(self):
        """Fetching an existing cohort returns it."""
        repo = FakeCohortRepository()
        cohort = make_cohort(repo)
        use_case = GetCohortUseCase(cohort_repository=repo)

        result = use_case.execute(GetCohortCommand(cohort_id=cohort.id))

        assert result.id == cohort.id
        assert result.name == "Batch 2024"

    def test_nonexistent_cohort_raises_error(self):
        """Fetching a nonexistent cohort raises CohortNotFoundError."""
        use_case = GetCohortUseCase(
            cohort_repository=FakeCohortRepository()
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(GetCohortCommand(cohort_id=uuid4()))


# ── ListCohorts Tests ─────────────────────────────────────────────────────

class TestListCohorts:

    def test_returns_all_cohorts(self):
        """Lists all cohorts when no filter provided."""
        repo = FakeCohortRepository()
        make_cohort(repo, status=CohortStatus.ACTIVE)
        make_cohort(repo, status=CohortStatus.ARCHIVED)
        use_case = ListCohortsUseCase(cohort_repository=repo)

        result = use_case.execute(ListCohortsCommand())

        assert len(result) == 2

    def test_filters_by_status(self):
        """Filters cohorts by status correctly."""
        repo = FakeCohortRepository()
        make_cohort(repo, status=CohortStatus.ACTIVE)
        make_cohort(repo, status=CohortStatus.ACTIVE)
        make_cohort(repo, status=CohortStatus.ARCHIVED)
        use_case = ListCohortsUseCase(cohort_repository=repo)

        result = use_case.execute(
            ListCohortsCommand(status=CohortStatus.ACTIVE)
        )

        assert len(result) == 2
        assert all(c.status == CohortStatus.ACTIVE for c in result)


# ── UpdateCohort Tests ────────────────────────────────────────────────────

class TestUpdateCohort:

    def test_updates_cohort_name(self):
        """Cohort name can be updated."""
        repo = FakeCohortRepository()
        cohort = make_cohort(repo)
        use_case = UpdateCohortUseCase(
            cohort_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(UpdateCohortCommand(
            cohort_id=cohort.id,
            name="Updated Batch",
        ))

        assert result.name == "Updated Batch"

    def test_updates_student_capacity(self):
        """Student capacity can be updated."""
        repo = FakeCohortRepository()
        cohort = make_cohort(repo, student_capacity=50)
        use_case = UpdateCohortUseCase(
            cohort_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(UpdateCohortCommand(
            cohort_id=cohort.id,
            student_capacity=100,
        ))

        assert result.student_capacity == 100

    def test_archived_cohort_cannot_be_updated(self):
        """Cannot update an archived cohort."""
        repo = FakeCohortRepository()
        cohort = make_cohort(repo, status=CohortStatus.ARCHIVED)
        use_case = UpdateCohortUseCase(
            cohort_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(CohortArchivedError):
            use_case.execute(UpdateCohortCommand(
                cohort_id=cohort.id,
                name="New Name",
            ))

    def test_publishes_cohort_updated_event(self):
        """CohortUpdated event must be published."""
        repo = FakeCohortRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(repo)
        use_case = UpdateCohortUseCase(
            cohort_repository=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(UpdateCohortCommand(
            cohort_id=cohort.id,
            name="Updated Batch",
        ))

        events = event_publisher.get_events_of_type("cohort_updated")
        assert len(events) == 1

    def test_nonexistent_cohort_raises_error(self):
        """Updating a nonexistent cohort raises error."""
        use_case = UpdateCohortUseCase(
            cohort_repository=FakeCohortRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(UpdateCohortCommand(
                cohort_id=uuid4(),
                name="New Name",
            ))


# ── ArchiveCohort Tests ───────────────────────────────────────────────────

class TestArchiveCohort:

    def test_archives_active_cohort(self):
        """ACTIVE cohort becomes ARCHIVED."""
        repo = FakeCohortRepository()
        cohort = make_cohort(repo, status=CohortStatus.ACTIVE)
        use_case = ArchiveCohortUseCase(
            cohort_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(ArchiveCohortCommand(cohort_id=cohort.id))

        assert result.status == CohortStatus.ARCHIVED

    def test_archiving_already_archived_is_safe(self):
        """Archiving an already archived cohort is idempotent."""
        repo = FakeCohortRepository()
        cohort = make_cohort(repo, status=CohortStatus.ARCHIVED)
        use_case = ArchiveCohortUseCase(
            cohort_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(ArchiveCohortCommand(cohort_id=cohort.id))

        assert result.status == CohortStatus.ARCHIVED

    def test_publishes_cohort_archived_event(self):
        """CohortArchived event must be published."""
        repo = FakeCohortRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(repo)
        use_case = ArchiveCohortUseCase(
            cohort_repository=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(ArchiveCohortCommand(cohort_id=cohort.id))

        events = event_publisher.get_events_of_type("cohort_archived")
        assert len(events) == 1

    def test_nonexistent_cohort_raises_error(self):
        """Archiving a nonexistent cohort raises error."""
        use_case = ArchiveCohortUseCase(
            cohort_repository=FakeCohortRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(ArchiveCohortCommand(cohort_id=uuid4()))


# ── AssignStudentToCohort Tests ───────────────────────────────────────────

class TestAssignStudentToCohort:

    def test_assigns_student_successfully(self):
        """Happy path — student gets assigned to cohort."""
        cohort_repo = FakeCohortRepository()
        student_repo = FakeStudentRepository()
        cohort = make_cohort(cohort_repo)
        student = make_student(student_repo)
        use_case = AssignStudentToCohortUseCase(
            cohort_repository=cohort_repo,
            student_repository=student_repo,
        )

        use_case.execute(AssignStudentToCohortCommand(
            cohort_id=cohort.id,
            student_id=student.id,
        ))

        assert cohort_repo.student_in_cohort(cohort.id, student.id)

    def test_enrolled_count_increases(self):
        """Enrolled count increases after assignment."""
        cohort_repo = FakeCohortRepository()
        student_repo = FakeStudentRepository()
        cohort = make_cohort(cohort_repo, enrolled_student_count=0)
        student = make_student(student_repo)
        use_case = AssignStudentToCohortUseCase(
            cohort_repository=cohort_repo,
            student_repository=student_repo,
        )

        use_case.execute(AssignStudentToCohortCommand(
            cohort_id=cohort.id,
            student_id=student.id,
        ))

        updated = cohort_repo.find_by_id(cohort.id)
        assert updated.enrolled_student_count == 1

    def test_duplicate_assignment_raises_error(self):
        """Assigning same student twice raises error."""
        cohort_repo = FakeCohortRepository()
        student_repo = FakeStudentRepository()
        cohort = make_cohort(cohort_repo)
        student = make_student(student_repo)
        use_case = AssignStudentToCohortUseCase(
            cohort_repository=cohort_repo,
            student_repository=student_repo,
        )

        use_case.execute(AssignStudentToCohortCommand(
            cohort_id=cohort.id,
            student_id=student.id,
        ))

        with pytest.raises(StudentAlreadyInCohortError):
            use_case.execute(AssignStudentToCohortCommand(
                cohort_id=cohort.id,
                student_id=student.id,
            ))

    def test_archived_cohort_raises_error(self):
        """Cannot assign student to archived cohort."""
        cohort_repo = FakeCohortRepository()
        student_repo = FakeStudentRepository()
        cohort = make_cohort(cohort_repo, status=CohortStatus.ARCHIVED)
        student = make_student(student_repo)
        use_case = AssignStudentToCohortUseCase(
            cohort_repository=cohort_repo,
            student_repository=student_repo,
        )

        with pytest.raises(CohortArchivedError):
            use_case.execute(AssignStudentToCohortCommand(
                cohort_id=cohort.id,
                student_id=student.id,
            ))

    def test_nonexistent_student_raises_error(self):
        """Assigning nonexistent student raises error."""
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = AssignStudentToCohortUseCase(
            cohort_repository=cohort_repo,
            student_repository=FakeStudentRepository(),
        )

        with pytest.raises(StudentNotFoundError):
            use_case.execute(AssignStudentToCohortCommand(
                cohort_id=cohort.id,
                student_id=uuid4(),
            ))

    def test_nonexistent_cohort_raises_error(self):
        """Assigning to nonexistent cohort raises error."""
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        use_case = AssignStudentToCohortUseCase(
            cohort_repository=FakeCohortRepository(),
            student_repository=student_repo,
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(AssignStudentToCohortCommand(
                cohort_id=uuid4(),
                student_id=student.id,
            ))


# ── AssignTeacherToCohort Tests ───────────────────────────────────────────

class TestAssignTeacherToCohort:

    def test_assigns_teacher_successfully(self):
        """Happy path — teacher gets assigned to cohort."""
        cohort_repo = FakeCohortRepository()
        teacher_repo = FakeTeacherRepository()
        cohort = make_cohort(cohort_repo)
        teacher = make_teacher(teacher_repo)
        event_publisher = FakeEventPublisher()
        use_case = AssignTeacherToCohortUseCase(
            cohort_repository=cohort_repo,
            teacher_repository=teacher_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(AssignTeacherToCohortCommand(
            cohort_id=cohort.id,
            teacher_id=teacher.id,
        ))

        assert cohort_repo.teacher_in_cohort(cohort.id, teacher.id)

    def test_teacher_count_increases(self):
        """Teacher count increases after assignment."""
        cohort_repo = FakeCohortRepository()
        teacher_repo = FakeTeacherRepository()
        cohort = make_cohort(cohort_repo, teacher_count=0)
        teacher = make_teacher(teacher_repo)
        use_case = AssignTeacherToCohortUseCase(
            cohort_repository=cohort_repo,
            teacher_repository=teacher_repo,
            event_publisher=FakeEventPublisher(),
        )

        use_case.execute(AssignTeacherToCohortCommand(
            cohort_id=cohort.id,
            teacher_id=teacher.id,
        ))

        updated = cohort_repo.find_by_id(cohort.id)
        assert updated.teacher_count == 1

    def test_publishes_teacher_assigned_event(self):
        """TeacherAssignedToCohort event must be published."""
        cohort_repo = FakeCohortRepository()
        teacher_repo = FakeTeacherRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(cohort_repo)
        teacher = make_teacher(teacher_repo)
        use_case = AssignTeacherToCohortUseCase(
            cohort_repository=cohort_repo,
            teacher_repository=teacher_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(AssignTeacherToCohortCommand(
            cohort_id=cohort.id,
            teacher_id=teacher.id,
        ))

        events = event_publisher.get_events_of_type("teacher_assigned_to_cohort")
        assert len(events) == 1

    def test_duplicate_assignment_raises_error(self):
        """Assigning same teacher twice raises error."""
        cohort_repo = FakeCohortRepository()
        teacher_repo = FakeTeacherRepository()
        cohort = make_cohort(cohort_repo)
        teacher = make_teacher(teacher_repo)
        use_case = AssignTeacherToCohortUseCase(
            cohort_repository=cohort_repo,
            teacher_repository=teacher_repo,
            event_publisher=FakeEventPublisher(),
        )

        use_case.execute(AssignTeacherToCohortCommand(
            cohort_id=cohort.id,
            teacher_id=teacher.id,
        ))

        with pytest.raises(TeacherAlreadyInCohortError):
            use_case.execute(AssignTeacherToCohortCommand(
                cohort_id=cohort.id,
                teacher_id=teacher.id,
            ))


# ── UnassignTeacherFromCohort Tests ──────────────────────────────────────

class TestUnassignTeacherFromCohort:

    def test_unassigns_teacher_successfully(self):
        """Teacher gets removed from cohort."""
        cohort_repo = FakeCohortRepository()
        teacher_repo = FakeTeacherRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(cohort_repo)
        teacher = make_teacher(teacher_repo)

        # Assign first
        cohort_repo.assign_teacher(cohort.id, teacher.id)

        use_case = UnassignTeacherFromCohortUseCase(
            cohort_repository=cohort_repo,
            teacher_repository=teacher_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(UnassignTeacherFromCohortCommand(
            cohort_id=cohort.id,
            teacher_id=teacher.id,
        ))

        assert not cohort_repo.teacher_in_cohort(cohort.id, teacher.id)

    def test_publishes_teacher_unassigned_event(self):
        """TeacherUnassignedFromCohort event must be published."""
        cohort_repo = FakeCohortRepository()
        teacher_repo = FakeTeacherRepository()
        event_publisher = FakeEventPublisher()
        cohort = make_cohort(cohort_repo)
        teacher = make_teacher(teacher_repo)
        cohort_repo.assign_teacher(cohort.id, teacher.id)

        use_case = UnassignTeacherFromCohortUseCase(
            cohort_repository=cohort_repo,
            teacher_repository=teacher_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(UnassignTeacherFromCohortCommand(
            cohort_id=cohort.id,
            teacher_id=teacher.id,
        ))

        events = event_publisher.get_events_of_type(
            "teacher_unassigned_from_cohort"
        )
        assert len(events) == 1

    def test_nonexistent_cohort_raises_error(self):
        """Unassigning from nonexistent cohort raises error."""
        teacher_repo = FakeTeacherRepository()
        teacher = make_teacher(teacher_repo)
        use_case = UnassignTeacherFromCohortUseCase(
            cohort_repository=FakeCohortRepository(),
            teacher_repository=teacher_repo,
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(UnassignTeacherFromCohortCommand(
                cohort_id=uuid4(),
                teacher_id=teacher.id,
            ))