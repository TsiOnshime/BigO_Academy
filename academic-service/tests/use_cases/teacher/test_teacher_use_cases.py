import pytest
from datetime import date
from uuid import uuid4

from domain.enums import TeacherStatus
from domain.exceptions import TeacherNotFoundError, TeacherAlreadyExistsError
from domain.models import Teacher
from application.use_cases.teacher.create_teacher import (
    CreateTeacherUseCase, CreateTeacherCommand,
)
from application.use_cases.teacher.get_teacher import (
    GetTeacherUseCase, GetTeacherCommand,
)
from application.use_cases.teacher.list_teachers import (
    ListTeachersUseCase, ListTeachersCommand,
)
from application.use_cases.teacher.update_teacher import (
    UpdateTeacherUseCase, UpdateTeacherCommand,
)
from application.use_cases.teacher.activate_teacher import (
    ActivateTeacherUseCase, ActivateTeacherCommand,
)
from application.use_cases.teacher.deactivate_teacher import (
    DeactivateTeacherUseCase, DeactivateTeacherCommand,
)
from tests.fakes import FakeTeacherRepository, FakeEventPublisher


# ── Helpers ───────────────────────────────────────────────────────────────

def make_teacher(repo: FakeTeacherRepository, **overrides) -> Teacher:
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "full_name": "Meron Tadesse",
        "email": "meron@a2sv.org",
        "status": TeacherStatus.PENDING,
        "assigned_cohort_ids": [],
    }
    defaults.update(overrides)
    teacher = Teacher(**defaults)
    repo.save(teacher)
    return teacher


# ── CreateTeacher Tests ───────────────────────────────────────────────────

class TestCreateTeacher:

    def test_creates_teacher_successfully(self):
        """Happy path — valid input creates a teacher."""
        repo = FakeTeacherRepository()
        event_publisher = FakeEventPublisher()
        use_case = CreateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=event_publisher,
        )

        result = use_case.execute(CreateTeacherCommand(
            user_id=uuid4(),
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
        ))

        assert result.teacher.full_name == "Meron Tadesse"
        assert result.teacher.email == "meron@a2sv.org"

    def test_new_teacher_starts_pending(self):
        """New teachers start as PENDING — admin must activate."""
        repo = FakeTeacherRepository()
        use_case = CreateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(CreateTeacherCommand(
            user_id=uuid4(),
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
        ))

        assert result.teacher.status == TeacherStatus.PENDING

    def test_new_teacher_has_no_cohorts(self):
        """New teachers have no cohort assignments."""
        repo = FakeTeacherRepository()
        use_case = CreateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(CreateTeacherCommand(
            user_id=uuid4(),
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
        ))

        assert result.teacher.assigned_cohort_ids == []

    def test_publishes_teacher_created_event(self):
        """TeacherCreated event must be published."""
        repo = FakeTeacherRepository()
        event_publisher = FakeEventPublisher()
        use_case = CreateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(CreateTeacherCommand(
            user_id=uuid4(),
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
        ))

        events = event_publisher.get_events_of_type("teacher_created")
        assert len(events) == 1

    def test_duplicate_user_id_raises_error(self):
        """Cannot create two teacher profiles for the same user."""
        repo = FakeTeacherRepository()
        use_case = CreateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=FakeEventPublisher(),
        )
        user_id = uuid4()

        use_case.execute(CreateTeacherCommand(
            user_id=user_id,
            full_name="Meron Tadesse",
            email="meron@a2sv.org",
        ))

        with pytest.raises(TeacherAlreadyExistsError):
            use_case.execute(CreateTeacherCommand(
                user_id=user_id,
                full_name="Meron Tadesse",
                email="meron@a2sv.org",
            ))


# ── GetTeacher Tests ──────────────────────────────────────────────────────

class TestGetTeacher:

    def test_returns_existing_teacher(self):
        """Fetching an existing teacher returns their profile."""
        repo = FakeTeacherRepository()
        teacher = make_teacher(repo)
        use_case = GetTeacherUseCase(teacher_repository=repo)

        result = use_case.execute(GetTeacherCommand(teacher_id=teacher.id))

        assert result.id == teacher.id
        assert result.full_name == "Meron Tadesse"

    def test_nonexistent_teacher_raises_error(self):
        """Fetching a nonexistent teacher raises TeacherNotFoundError."""
        use_case = GetTeacherUseCase(
            teacher_repository=FakeTeacherRepository()
        )

        with pytest.raises(TeacherNotFoundError):
            use_case.execute(GetTeacherCommand(teacher_id=uuid4()))


# ── ListTeachers Tests ────────────────────────────────────────────────────

class TestListTeachers:

    def test_returns_all_teachers(self):
        """Lists all teachers when no filter provided."""
        repo = FakeTeacherRepository()
        make_teacher(repo, status=TeacherStatus.PENDING)
        make_teacher(repo, status=TeacherStatus.ACTIVE)
        make_teacher(repo, status=TeacherStatus.INACTIVE)
        use_case = ListTeachersUseCase(teacher_repository=repo)

        result = use_case.execute(ListTeachersCommand())

        assert len(result) == 3

    def test_filters_by_status(self):
        """Filters teachers by status correctly."""
        repo = FakeTeacherRepository()
        make_teacher(repo, status=TeacherStatus.ACTIVE)
        make_teacher(repo, status=TeacherStatus.ACTIVE)
        make_teacher(repo, status=TeacherStatus.INACTIVE)
        use_case = ListTeachersUseCase(teacher_repository=repo)

        result = use_case.execute(
            ListTeachersCommand(status=TeacherStatus.ACTIVE)
        )

        assert len(result) == 2
        assert all(t.status == TeacherStatus.ACTIVE for t in result)


# ── UpdateTeacher Tests ───────────────────────────────────────────────────

class TestUpdateTeacher:

    def test_updates_full_name(self):
        """Full name can be updated."""
        repo = FakeTeacherRepository()
        teacher = make_teacher(repo)
        use_case = UpdateTeacherUseCase(teacher_repository=repo)

        result = use_case.execute(UpdateTeacherCommand(
            teacher_id=teacher.id,
            full_name="Updated Name",
        ))

        assert result.full_name == "Updated Name"

    def test_updates_email(self):
        """Email can be updated."""
        repo = FakeTeacherRepository()
        teacher = make_teacher(repo)
        use_case = UpdateTeacherUseCase(teacher_repository=repo)

        result = use_case.execute(UpdateTeacherCommand(
            teacher_id=teacher.id,
            email="updated@a2sv.org",
        ))

        assert result.email == "updated@a2sv.org"

    def test_nonexistent_teacher_raises_error(self):
        """Updating a nonexistent teacher raises error."""
        use_case = UpdateTeacherUseCase(
            teacher_repository=FakeTeacherRepository()
        )

        with pytest.raises(TeacherNotFoundError):
            use_case.execute(UpdateTeacherCommand(
                teacher_id=uuid4(),
                full_name="New Name",
            ))


# ── ActivateTeacher Tests ─────────────────────────────────────────────────

class TestActivateTeacher:

    def test_activates_pending_teacher(self):
        """PENDING teacher becomes ACTIVE after activation."""
        repo = FakeTeacherRepository()
        teacher = make_teacher(repo, status=TeacherStatus.PENDING)
        use_case = ActivateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(ActivateTeacherCommand(
            teacher_id=teacher.id
        ))

        assert result.status == TeacherStatus.ACTIVE

    def test_activating_already_active_is_safe(self):
        """Activating an already active teacher is idempotent."""
        repo = FakeTeacherRepository()
        teacher = make_teacher(repo, status=TeacherStatus.ACTIVE)
        use_case = ActivateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(ActivateTeacherCommand(
            teacher_id=teacher.id
        ))

        assert result.status == TeacherStatus.ACTIVE

    def test_publishes_teacher_status_changed_event(self):
        """Activation publishes TeacherStatusChanged event."""
        repo = FakeTeacherRepository()
        event_publisher = FakeEventPublisher()
        teacher = make_teacher(repo, status=TeacherStatus.PENDING)
        use_case = ActivateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(ActivateTeacherCommand(teacher_id=teacher.id))

        events = event_publisher.get_events_of_type("teacher_status_changed")
        assert len(events) == 1

    def test_nonexistent_teacher_raises_error(self):
        """Activating a nonexistent teacher raises error."""
        use_case = ActivateTeacherUseCase(
            teacher_repository=FakeTeacherRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(TeacherNotFoundError):
            use_case.execute(ActivateTeacherCommand(teacher_id=uuid4()))


# ── DeactivateTeacher Tests ───────────────────────────────────────────────

class TestDeactivateTeacher:

    def test_deactivates_active_teacher(self):
        """ACTIVE teacher becomes INACTIVE after deactivation."""
        repo = FakeTeacherRepository()
        teacher = make_teacher(repo, status=TeacherStatus.ACTIVE)
        use_case = DeactivateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(DeactivateTeacherCommand(
            teacher_id=teacher.id
        ))

        assert result.status == TeacherStatus.INACTIVE

    def test_publishes_teacher_status_changed_event(self):
        """Deactivation publishes TeacherStatusChanged event."""
        repo = FakeTeacherRepository()
        event_publisher = FakeEventPublisher()
        teacher = make_teacher(repo, status=TeacherStatus.ACTIVE)
        use_case = DeactivateTeacherUseCase(
            teacher_repository=repo,
            event_publisher=event_publisher,
        )

        use_case.execute(DeactivateTeacherCommand(teacher_id=teacher.id))

        events = event_publisher.get_events_of_type("teacher_status_changed")
        assert len(events) == 1

    def test_nonexistent_teacher_raises_error(self):
        """Deactivating a nonexistent teacher raises error."""
        use_case = DeactivateTeacherUseCase(
            teacher_repository=FakeTeacherRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(TeacherNotFoundError):
            use_case.execute(DeactivateTeacherCommand(teacher_id=uuid4()))
            