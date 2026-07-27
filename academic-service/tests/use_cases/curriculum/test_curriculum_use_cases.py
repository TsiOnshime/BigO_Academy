import pytest
from uuid import uuid4
from datetime import date

from domain.enums import (
    YearPhase, ProblemSource, ProblemDifficulty, CohortStatus,
)
from domain.exceptions import (
    TopicNotFoundError, ProblemNotFoundError, CohortNotFoundError,
)
from domain.models import Cohort, Topic, Problem
from application.use_cases.curriculum.create_topic import (
    CreateTopicUseCase, CreateTopicCommand,
)
from application.use_cases.curriculum.get_topic import (
    GetTopicUseCase, GetTopicCommand,
)
from application.use_cases.curriculum.list_topics import (
    ListTopicsUseCase, ListTopicsCommand,
)
from application.use_cases.curriculum.update_topic import (
    UpdateTopicUseCase, UpdateTopicCommand,
)
from application.use_cases.curriculum.delete_topic import (
    DeleteTopicUseCase, DeleteTopicCommand,
)
from application.use_cases.curriculum.reorder_topics import (
    ReorderTopicsUseCase, ReorderTopicsCommand,
)
from application.use_cases.curriculum.add_problem import (
    AddProblemUseCase, AddProblemCommand,
)
from application.use_cases.curriculum.update_problem import (
    UpdateProblemUseCase, UpdateProblemCommand,
)
from application.use_cases.curriculum.delete_problem import (
    DeleteProblemUseCase, DeleteProblemCommand,
)
from tests.fakes import FakeCurriculumRepository, FakeCohortRepository


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


def make_topic(
    curriculum_repo: FakeCurriculumRepository,
    cohort_id,
    **overrides,
) -> Topic:
    defaults = {
        "id": uuid4(),
        "curriculum_id": cohort_id,
        "title": "Binary Trees",
        "description": "Tree data structures",
        "year_phase": YearPhase.YEAR_ONE,
        "display_order": 0,
        "problem_count": 0,
    }
    defaults.update(overrides)
    topic = Topic(**defaults)
    curriculum_repo.save_topic(topic)
    return topic


def make_problem(
    curriculum_repo: FakeCurriculumRepository,
    topic_id,
    **overrides,
) -> Problem:
    defaults = {
        "id": uuid4(),
        "topic_id": topic_id,
        "title": "Two Sum",
        "source": ProblemSource.LEETCODE,
        "external_url": "https://leetcode.com/problems/two-sum/",
        "difficulty": ProblemDifficulty.EASY,
    }
    defaults.update(overrides)
    problem = Problem(**defaults)
    curriculum_repo.save_problem(problem)
    return problem


# ── CreateTopic Tests ─────────────────────────────────────────────────────

class TestCreateTopic:

    def test_creates_topic_successfully(self):
        """Happy path — valid input creates a topic."""
        curriculum_repo = FakeCurriculumRepository()
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = CreateTopicUseCase(
            curriculum_repository=curriculum_repo,
            cohort_repository=cohort_repo,
        )

        result = use_case.execute(CreateTopicCommand(
            cohort_id=cohort.id,
            title="Binary Trees",
            year_phase=YearPhase.YEAR_ONE,
        ))

        assert result.title == "Binary Trees"
        assert result.year_phase == YearPhase.YEAR_ONE

    def test_nonexistent_cohort_raises_error(self):
        """Creating topic for nonexistent cohort raises error."""
        use_case = CreateTopicUseCase(
            curriculum_repository=FakeCurriculumRepository(),
            cohort_repository=FakeCohortRepository(),
        )

        with pytest.raises(CohortNotFoundError):
            use_case.execute(CreateTopicCommand(
                cohort_id=uuid4(),
                title="Binary Trees",
                year_phase=YearPhase.YEAR_ONE,
            ))

    def test_topic_saved_to_repository(self):
        """Created topic must be findable in the repo."""
        curriculum_repo = FakeCurriculumRepository()
        cohort_repo = FakeCohortRepository()
        cohort = make_cohort(cohort_repo)
        use_case = CreateTopicUseCase(
            curriculum_repository=curriculum_repo,
            cohort_repository=cohort_repo,
        )

        result = use_case.execute(CreateTopicCommand(
            cohort_id=cohort.id,
            title="Binary Trees",
            year_phase=YearPhase.YEAR_ONE,
        ))

        found = curriculum_repo.find_topic_by_id(result.id)
        assert found is not None


# ── GetTopic Tests ────────────────────────────────────────────────────────

class TestGetTopic:

    def test_returns_existing_topic(self):
        """Fetching an existing topic returns it."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        use_case = GetTopicUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(GetTopicCommand(topic_id=topic.id))

        assert result.id == topic.id
        assert result.title == "Binary Trees"

    def test_nonexistent_topic_raises_error(self):
        """Fetching nonexistent topic raises TopicNotFoundError."""
        use_case = GetTopicUseCase(
            curriculum_repository=FakeCurriculumRepository()
        )

        with pytest.raises(TopicNotFoundError):
            use_case.execute(GetTopicCommand(topic_id=uuid4()))


# ── ListTopics Tests ──────────────────────────────────────────────────────

class TestListTopics:

    def test_returns_topics_for_cohort(self):
        """Lists all topics for a cohort."""
        curriculum_repo = FakeCurriculumRepository()
        cohort_id = uuid4()
        make_topic(curriculum_repo, cohort_id, title="Topic 1")
        make_topic(curriculum_repo, cohort_id, title="Topic 2")
        make_topic(curriculum_repo, uuid4(), title="Other Cohort Topic")
        use_case = ListTopicsUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(ListTopicsCommand(cohort_id=cohort_id))

        assert len(result) == 2

    def test_filters_by_year_phase(self):
        """Filters topics by year phase."""
        curriculum_repo = FakeCurriculumRepository()
        cohort_id = uuid4()
        make_topic(curriculum_repo, cohort_id, year_phase=YearPhase.YEAR_ONE)
        make_topic(curriculum_repo, cohort_id, year_phase=YearPhase.YEAR_ONE)
        make_topic(curriculum_repo, cohort_id, year_phase=YearPhase.YEAR_TWO)
        use_case = ListTopicsUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(ListTopicsCommand(
            cohort_id=cohort_id,
            year_phase=YearPhase.YEAR_ONE,
        ))

        assert len(result) == 2
        assert all(t.year_phase == YearPhase.YEAR_ONE for t in result)

    def test_returns_topics_ordered_by_display_order(self):
        """Topics are returned in display_order ascending."""
        curriculum_repo = FakeCurriculumRepository()
        cohort_id = uuid4()
        make_topic(curriculum_repo, cohort_id, display_order=2, title="C")
        make_topic(curriculum_repo, cohort_id, display_order=0, title="A")
        make_topic(curriculum_repo, cohort_id, display_order=1, title="B")
        use_case = ListTopicsUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(ListTopicsCommand(cohort_id=cohort_id))

        assert result[0].title == "A"
        assert result[1].title == "B"
        assert result[2].title == "C"


# ── UpdateTopic Tests ─────────────────────────────────────────────────────

class TestUpdateTopic:

    def test_updates_title(self):
        """Topic title can be updated."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        use_case = UpdateTopicUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(UpdateTopicCommand(
            topic_id=topic.id,
            title="Updated Title",
        ))

        assert result.title == "Updated Title"

    def test_updates_display_order(self):
        """Topic display order can be updated."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4(), display_order=0)
        use_case = UpdateTopicUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(UpdateTopicCommand(
            topic_id=topic.id,
            display_order=5,
        ))

        assert result.display_order == 5

    def test_nonexistent_topic_raises_error(self):
        """Updating nonexistent topic raises error."""
        use_case = UpdateTopicUseCase(
            curriculum_repository=FakeCurriculumRepository()
        )

        with pytest.raises(TopicNotFoundError):
            use_case.execute(UpdateTopicCommand(
                topic_id=uuid4(),
                title="New Title",
            ))


# ── DeleteTopic Tests ─────────────────────────────────────────────────────

class TestDeleteTopic:

    def test_deletes_topic_successfully(self):
        """Topic is removed from repository after deletion."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        use_case = DeleteTopicUseCase(curriculum_repository=curriculum_repo)

        use_case.execute(DeleteTopicCommand(topic_id=topic.id))

        assert curriculum_repo.find_topic_by_id(topic.id) is None

    def test_deletes_cascade_to_problems(self):
        """Deleting a topic also deletes its problems."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        problem = make_problem(curriculum_repo, topic.id)
        use_case = DeleteTopicUseCase(curriculum_repository=curriculum_repo)

        use_case.execute(DeleteTopicCommand(topic_id=topic.id))

        assert curriculum_repo.find_problem_by_id(problem.id) is None

    def test_nonexistent_topic_raises_error(self):
        """Deleting nonexistent topic raises error."""
        use_case = DeleteTopicUseCase(
            curriculum_repository=FakeCurriculumRepository()
        )

        with pytest.raises(TopicNotFoundError):
            use_case.execute(DeleteTopicCommand(topic_id=uuid4()))


# ── ReorderTopics Tests ───────────────────────────────────────────────────

class TestReorderTopics:

    def test_reorders_topics_by_list_position(self):
        """Topics get new display_order based on list position."""
        curriculum_repo = FakeCurriculumRepository()
        cohort_id = uuid4()
        t1 = make_topic(curriculum_repo, cohort_id, display_order=2)
        t2 = make_topic(curriculum_repo, cohort_id, display_order=0)
        t3 = make_topic(curriculum_repo, cohort_id, display_order=1)
        use_case = ReorderTopicsUseCase(
            curriculum_repository=curriculum_repo
        )

        use_case.execute(ReorderTopicsCommand(
            ordered_topic_ids=[t2.id, t3.id, t1.id]
        ))

        assert curriculum_repo.find_topic_by_id(t2.id).display_order == 0
        assert curriculum_repo.find_topic_by_id(t3.id).display_order == 1
        assert curriculum_repo.find_topic_by_id(t1.id).display_order == 2


# ── AddProblem Tests ──────────────────────────────────────────────────────

class TestAddProblem:

    def test_adds_problem_successfully(self):
        """Problem is added to topic successfully."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        use_case = AddProblemUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(AddProblemCommand(
            topic_id=topic.id,
            title="Two Sum",
            source=ProblemSource.LEETCODE,
            external_url="https://leetcode.com/problems/two-sum/",
            difficulty=ProblemDifficulty.EASY,
        ))

        assert result.title == "Two Sum"
        assert result.source == ProblemSource.LEETCODE
        assert result.topic_id == topic.id

    def test_nonexistent_topic_raises_error(self):
        """Adding problem to nonexistent topic raises error."""
        use_case = AddProblemUseCase(
            curriculum_repository=FakeCurriculumRepository()
        )

        with pytest.raises(TopicNotFoundError):
            use_case.execute(AddProblemCommand(
                topic_id=uuid4(),
                title="Two Sum",
                source=ProblemSource.LEETCODE,
                external_url="https://leetcode.com/problems/two-sum/",
                difficulty=ProblemDifficulty.EASY,
            ))


# ── UpdateProblem Tests ───────────────────────────────────────────────────

class TestUpdateProblem:

    def test_updates_problem_title(self):
        """Problem title can be updated."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        problem = make_problem(curriculum_repo, topic.id)
        use_case = UpdateProblemUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(UpdateProblemCommand(
            problem_id=problem.id,
            title="Updated Problem",
        ))

        assert result.title == "Updated Problem"

    def test_updates_difficulty(self):
        """Problem difficulty can be updated."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        problem = make_problem(
            curriculum_repo, topic.id, difficulty=ProblemDifficulty.EASY
        )
        use_case = UpdateProblemUseCase(curriculum_repository=curriculum_repo)

        result = use_case.execute(UpdateProblemCommand(
            problem_id=problem.id,
            difficulty=ProblemDifficulty.HARD,
        ))

        assert result.difficulty == ProblemDifficulty.HARD

    def test_nonexistent_problem_raises_error(self):
        """Updating nonexistent problem raises error."""
        use_case = UpdateProblemUseCase(
            curriculum_repository=FakeCurriculumRepository()
        )

        with pytest.raises(ProblemNotFoundError):
            use_case.execute(UpdateProblemCommand(
                problem_id=uuid4(),
                title="New Title",
            ))


# ── DeleteProblem Tests ───────────────────────────────────────────────────

class TestDeleteProblem:

    def test_deletes_problem_successfully(self):
        """Problem is removed from repository after deletion."""
        curriculum_repo = FakeCurriculumRepository()
        topic = make_topic(curriculum_repo, uuid4())
        problem = make_problem(curriculum_repo, topic.id)
        use_case = DeleteProblemUseCase(curriculum_repository=curriculum_repo)

        use_case.execute(DeleteProblemCommand(problem_id=problem.id))

        assert curriculum_repo.find_problem_by_id(problem.id) is None

    def test_nonexistent_problem_raises_error(self):
        """Deleting nonexistent problem raises error."""
        use_case = DeleteProblemUseCase(
            curriculum_repository=FakeCurriculumRepository()
        )

        with pytest.raises(ProblemNotFoundError):
            use_case.execute(DeleteProblemCommand(problem_id=uuid4()))