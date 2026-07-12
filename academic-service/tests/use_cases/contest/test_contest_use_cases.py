import pytest
from uuid import uuid4
from datetime import datetime, timezone, date

from domain.enums import ContestStatus, CohortStatus
from domain.exceptions import (
    ContestNotFoundError,
    ContestResultsAlreadySubmittedError,
    CohortNotFoundError,
)
from domain.models import Cohort, Contest, ContestResult
from application.use_cases.contest.create_contest import (
    CreateContestUseCase, CreateContestCommand,
)
from application.use_cases.contest.list_contests import (
    ListContestsUseCase, ListContestsCommand,
)
from application.use_cases.contest.get_contest import (
    GetContestUseCase, GetContestCommand,
)
from application.use_cases.contest.get_contest_results import (
    GetContestResultsUseCase, GetContestResultsCommand,
)
from application.use_cases.contest.submit_contest_results import (
    SubmitContestResultsUseCase, SubmitContestResultsCommand,
    ContestResultInput,
)
from tests.fakes import (
    FakeContestRepository,
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


def make_contest(repo: FakeContestRepository, cohort_id, **overrides) -> Contest:
    defaults = {
        "id": uuid4(),
        "title": "Weekly Contest #1",
        "cohort_id": cohort_id,
        "external_contest_url": "https://codeforces.com/contest/1234",
        "status": ContestStatus.UPCOMING,
        "scheduled_at": datetime.now(timezone.utc),
        "ended_at": None,
        "problem_count": 4,
        "results": [],
    }
    defaults.update(overrides)
    contest = Contest(**defaults)
    repo.save(contest)
    return contest


def make_result_input(student_id=None, **overrides) -> ContestResultInput:
    defaults = {
        "student_id": student_id or uuid4(),
        "student_name": "Abel Girma",
        "contest_rank": 1,
        "problems_solved": 3,
        "participated": True,
    }
    defaults.update(overrides)
    return ContestResultInput(**defaults)


# ── CreateContest Tests ───────────────────────────────────────────────────

class TestCreateContest:

    def test_creates_contest_successfully(self):
        """Happy path — valid input creates a contest."""
        cohort_repo = FakeCohortRepository()
        contest_repo = FakeContestRepository()
        cohort = make_cohort(cohort_repo)
        use_case = CreateContestUseCase(
            contest_repository=contest_repo,
            cohort_repository=cohort_repo,
        )

        result = use_case.execute(CreateContestCommand(
            title="Weekly Contest #1",
            cohort_id=cohort.id,
            external_contest_url="https://codeforces.com/contest/1234",
            scheduled_at=datetime.now(timezone.utc),
        ))

        assert result.title == "Weekly Contest #1"
        assert result.status == ContestStatus.UPCOMING

    def test_new_contest_starts_upcoming(self):
        """New contests start with UPCOMING status."""
        cohort_repo = FakeCohortRepository()
        contest_repo = FakeContestRepository()
        cohort = make_cohort(cohort_repo)
        use_case = CreateContestUseCase(
            contest_repository=contest_repo,
            cohort_repository=cohort_repo,
        )

        result = use_case.execute(CreateContestCommand(
            title="Weekly Contest #1",
            cohort_id=cohort.id,
            external_contest_url="https://codeforces.com/contest/1234",
            scheduled_at=datetime.now(timezone.utc),
        ))

        assert result.status == ContestStatus.UPCOMING

    def test_nonexistent_cohort_raises_error(self):
        """Creating contest for nonexistent cohort raises error."""
        use_case = CreateContestUseCase(
            contest_repository=FakeContestRepository(),
            cohort_repository=FakeCohortRepository(),
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(CreateContestCommand(
                title="Weekly Contest #1",
                cohort_id=uuid4(),
                external_contest_url="https://codeforces.com/contest/1234",
                scheduled_at=datetime.now(timezone.utc),
            ))


# ── ListContests Tests ────────────────────────────────────────────────────

class TestListContests:

    def test_returns_contests_for_cohort(self):
        """Lists all contests for a cohort."""
        contest_repo = FakeContestRepository()
        cohort_id = uuid4()
        make_contest(contest_repo, cohort_id)
        make_contest(contest_repo, cohort_id)
        make_contest(contest_repo, uuid4())  # other cohort
        use_case = ListContestsUseCase(contest_repository=contest_repo)

        result = use_case.execute(ListContestsCommand(cohort_id=cohort_id))

        assert len(result) == 2

    def test_filters_by_status(self):
        """Filters contests by status."""
        contest_repo = FakeContestRepository()
        cohort_id = uuid4()
        make_contest(contest_repo, cohort_id, status=ContestStatus.UPCOMING)
        make_contest(contest_repo, cohort_id, status=ContestStatus.FINISHED)
        use_case = ListContestsUseCase(contest_repository=contest_repo)

        result = use_case.execute(ListContestsCommand(
            cohort_id=cohort_id,
            status=ContestStatus.FINISHED,
        ))

        assert len(result) == 1
        assert result[0].status == ContestStatus.FINISHED


# ── GetContest Tests ──────────────────────────────────────────────────────

class TestGetContest:

    def test_returns_existing_contest(self):
        """Fetching an existing contest returns it."""
        contest_repo = FakeContestRepository()
        contest = make_contest(contest_repo, uuid4())
        use_case = GetContestUseCase(contest_repository=contest_repo)

        result = use_case.execute(GetContestCommand(contest_id=contest.id))

        assert result.id == contest.id
        assert result.title == "Weekly Contest #1"

    def test_nonexistent_contest_raises_error(self):
        """Fetching nonexistent contest raises error."""
        use_case = GetContestUseCase(
            contest_repository=FakeContestRepository()
        )

        with pytest.raises(ContestNotFoundError):
            use_case.execute(GetContestCommand(contest_id=uuid4()))


# ── GetContestResults Tests ───────────────────────────────────────────────

class TestGetContestResults:

    def test_returns_results_for_contest(self):
        """Returns all results for a finished contest."""
        contest_repo = FakeContestRepository()
        contest = make_contest(
            contest_repo, uuid4(), status=ContestStatus.FINISHED
        )
        contest_repo.save_results(contest.id, [
            ContestResult(
                student_id=uuid4(),
                student_name="Abel",
                contest_rank=1,
                problems_solved=4,
                participated=True,
            ),
            ContestResult(
                student_id=uuid4(),
                student_name="Meron",
                contest_rank=2,
                problems_solved=3,
                participated=True,
            ),
        ])
        use_case = GetContestResultsUseCase(contest_repository=contest_repo)

        result = use_case.execute(
            GetContestResultsCommand(contest_id=contest.id)
        )

        assert len(result) == 2

    def test_nonexistent_contest_raises_error(self):
        """Fetching results for nonexistent contest raises error."""
        use_case = GetContestResultsUseCase(
            contest_repository=FakeContestRepository()
        )

        with pytest.raises(ContestNotFoundError):
            use_case.execute(GetContestResultsCommand(contest_id=uuid4()))


# ── SubmitContestResults Tests ────────────────────────────────────────────

class TestSubmitContestResults:

    def test_submits_results_successfully(self):
        """Happy path — results submitted and contest marked FINISHED."""
        contest_repo = FakeContestRepository()
        event_publisher = FakeEventPublisher()
        contest = make_contest(contest_repo, uuid4())
        use_case = SubmitContestResultsUseCase(
            contest_repository=contest_repo,
            event_publisher=event_publisher,
        )

        result = use_case.execute(SubmitContestResultsCommand(
            contest_id=contest.id,
            results=[make_result_input()],
        ))

        assert result.status == ContestStatus.FINISHED

    def test_contest_marked_finished_after_submission(self):
        """Contest status becomes FINISHED after results submitted."""
        contest_repo = FakeContestRepository()
        contest = make_contest(contest_repo, uuid4())
        use_case = SubmitContestResultsUseCase(
            contest_repository=contest_repo,
            event_publisher=FakeEventPublisher(),
        )

        use_case.execute(SubmitContestResultsCommand(
            contest_id=contest.id,
            results=[make_result_input()],
        ))

        updated = contest_repo.find_by_id(contest.id)
        assert updated.status == ContestStatus.FINISHED

    def test_ended_at_set_after_submission(self):
        """ended_at timestamp is set when results are submitted."""
        contest_repo = FakeContestRepository()
        contest = make_contest(contest_repo, uuid4(), ended_at=None)
        use_case = SubmitContestResultsUseCase(
            contest_repository=contest_repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(SubmitContestResultsCommand(
            contest_id=contest.id,
            results=[make_result_input()],
        ))

        assert result.ended_at is not None

    def test_publishes_contest_finished_event(self):
        """ContestFinished event must be published."""
        contest_repo = FakeContestRepository()
        event_publisher = FakeEventPublisher()
        contest = make_contest(contest_repo, uuid4())
        use_case = SubmitContestResultsUseCase(
            contest_repository=contest_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(SubmitContestResultsCommand(
            contest_id=contest.id,
            results=[make_result_input()],
        ))

        events = event_publisher.get_events_of_type("contest_finished")
        assert len(events) == 1

    def test_duplicate_submission_raises_error(self):
        """Submitting results twice raises ContestResultsAlreadySubmittedError."""
        contest_repo = FakeContestRepository()
        contest = make_contest(contest_repo, uuid4())
        use_case = SubmitContestResultsUseCase(
            contest_repository=contest_repo,
            event_publisher=FakeEventPublisher(),
        )

        use_case.execute(SubmitContestResultsCommand(
            contest_id=contest.id,
            results=[make_result_input()],
        ))

        with pytest.raises(ContestResultsAlreadySubmittedError):
            use_case.execute(SubmitContestResultsCommand(
                contest_id=contest.id,
                results=[make_result_input()],
            ))

    def test_nonexistent_contest_raises_error(self):
        """Submitting results for nonexistent contest raises error."""
        use_case = SubmitContestResultsUseCase(
            contest_repository=FakeContestRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(ContestNotFoundError):
            use_case.execute(SubmitContestResultsCommand(
                contest_id=uuid4(),
                results=[make_result_input()],
            ))