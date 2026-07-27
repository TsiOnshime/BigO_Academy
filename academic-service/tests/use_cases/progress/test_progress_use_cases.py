import pytest
from uuid import uuid4
from datetime import date

from domain.enums import (
    StudentStatus, YearPhase, ProblemSource, ProblemDifficulty,
)
from domain.exceptions import StudentNotFoundError, ProblemNotFoundError
from domain.models import Student, Problem, ProblemProgress
from application.use_cases.progress.get_student_progress import (
    GetStudentProgressUseCase, GetStudentProgressCommand,
)
from application.use_cases.progress.update_problem_progress import (
    UpdateProblemProgressUseCase, UpdateProblemProgressCommand,
)
from tests.fakes import (
    FakeStudentRepository,
    FakeCurriculumRepository,
    FakeProgressRepository,
    FakeEventPublisher,
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


def make_problem(
    curriculum_repo: FakeCurriculumRepository, **overrides
) -> Problem:
    defaults = {
        "id": uuid4(),
        "topic_id": uuid4(),
        "title": "Two Sum",
        "source": ProblemSource.LEETCODE,
        "external_url": "https://leetcode.com/problems/two-sum/",
        "difficulty": ProblemDifficulty.EASY,
    }
    defaults.update(overrides)
    problem = Problem(**defaults)
    curriculum_repo.save_problem(problem)
    return problem


def make_progress(
    progress_repo: FakeProgressRepository,
    student_id,
    problem_id,
    **overrides,
) -> ProblemProgress:
    defaults = {
        "id": uuid4(),
        "student_id": student_id,
        "problem_id": problem_id,
        "solved": False,
        "attempt_count": 0,
        "solve_time_minutes": 0,
        "verified_by_teacher": False,
        "solved_at": None,
    }
    defaults.update(overrides)
    progress = ProblemProgress(**defaults)
    progress_repo.save(progress)
    return progress


# ── GetStudentProgress Tests ──────────────────────────────────────────────

class TestGetStudentProgress:

    def test_returns_progress_for_student(self):
        """Returns all progress records for a student."""
        student_repo = FakeStudentRepository()
        curriculum_repo = FakeCurriculumRepository()
        progress_repo = FakeProgressRepository()
        student = make_student(student_repo)
        p1 = make_problem(curriculum_repo)
        p2 = make_problem(curriculum_repo)
        make_progress(progress_repo, student.id, p1.id, solved=True)
        make_progress(progress_repo, student.id, p2.id, solved=False)
        use_case = GetStudentProgressUseCase(
            student_repository=student_repo,
            progress_repository=progress_repo,
        )

        result = use_case.execute(
            GetStudentProgressCommand(student_id=student.id)
        )

        assert result.total_problems == 2
        assert result.solved_count == 1

    def test_calculates_completion_percentage(self):
        """Completion percentage is calculated correctly."""
        student_repo = FakeStudentRepository()
        progress_repo = FakeProgressRepository()
        curriculum_repo = FakeCurriculumRepository()
        student = make_student(student_repo)

        for i in range(3):
            p = make_problem(curriculum_repo)
            make_progress(
                progress_repo, student.id, p.id,
                solved=(i < 2)   # 2 out of 3 solved
            )

        use_case = GetStudentProgressUseCase(
            student_repository=student_repo,
            progress_repository=progress_repo,
        )

        result = use_case.execute(
            GetStudentProgressCommand(student_id=student.id)
        )

        assert result.completion_percentage == pytest.approx(66.67, rel=0.01)

    def test_zero_problems_returns_zero_percentage(self):
        """Student with no problems has 0% completion."""
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        use_case = GetStudentProgressUseCase(
            student_repository=student_repo,
            progress_repository=FakeProgressRepository(),
        )

        result = use_case.execute(
            GetStudentProgressCommand(student_id=student.id)
        )

        assert result.total_problems == 0
        assert result.solved_count == 0
        assert result.completion_percentage == 0.0

    def test_nonexistent_student_raises_error(self):
        """Fetching progress for nonexistent student raises error."""
        use_case = GetStudentProgressUseCase(
            student_repository=FakeStudentRepository(),
            progress_repository=FakeProgressRepository(),
        )

        with pytest.raises(StudentNotFoundError):
            use_case.execute(
                GetStudentProgressCommand(student_id=uuid4())
            )


# ── UpdateProblemProgress Tests ───────────────────────────────────────────

class TestUpdateProblemProgress:

    def test_marks_problem_as_solved(self):
        """Student can mark a problem as solved."""
        student_repo = FakeStudentRepository()
        curriculum_repo = FakeCurriculumRepository()
        progress_repo = FakeProgressRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(student_repo)
        problem = make_problem(curriculum_repo)
        use_case = UpdateProblemProgressUseCase(
            student_repository=student_repo,
            curriculum_repository=curriculum_repo,
            progress_repository=progress_repo,
            event_publisher=event_publisher,
        )

        result = use_case.execute(UpdateProblemProgressCommand(
            student_id=student.id,
            problem_id=problem.id,
            solved=True,
            attempt_count=2,
            solve_time_minutes=30,
        ))

        assert result.solved is True
        assert result.attempt_count == 2
        assert result.solve_time_minutes == 30

    def test_publishes_problem_solved_event_on_first_solve(self):
        """ProblemSolved event is published when first solved."""
        student_repo = FakeStudentRepository()
        curriculum_repo = FakeCurriculumRepository()
        progress_repo = FakeProgressRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(student_repo)
        problem = make_problem(curriculum_repo)
        use_case = UpdateProblemProgressUseCase(
            student_repository=student_repo,
            curriculum_repository=curriculum_repo,
            progress_repository=progress_repo,
            event_publisher=event_publisher,
        )

        use_case.execute(UpdateProblemProgressCommand(
            student_id=student.id,
            problem_id=problem.id,
            solved=True,
        ))

        events = event_publisher.get_events_of_type("problem_solved")
        assert len(events) == 1

    def test_does_not_publish_event_on_re_solve(self):
        """ProblemSolved event is NOT published if already solved."""
        student_repo = FakeStudentRepository()
        curriculum_repo = FakeCurriculumRepository()
        progress_repo = FakeProgressRepository()
        event_publisher = FakeEventPublisher()
        student = make_student(student_repo)
        problem = make_problem(curriculum_repo)
        # Pre-existing solved progress
        make_progress(
            progress_repo, student.id, problem.id, solved=True
        )
        use_case = UpdateProblemProgressUseCase(
            student_repository=student_repo,
            curriculum_repository=curriculum_repo,
            progress_repository=progress_repo,
            event_publisher=event_publisher,
        )

        # Mark as solved again
        use_case.execute(UpdateProblemProgressCommand(
            student_id=student.id,
            problem_id=problem.id,
            solved=True,
            attempt_count=5,
        ))

        # No new event — already counted
        events = event_publisher.get_events_of_type("problem_solved")
        assert len(events) == 0

    def test_solved_at_set_on_first_solve(self):
        """solved_at timestamp is set when first solved."""
        student_repo = FakeStudentRepository()
        curriculum_repo = FakeCurriculumRepository()
        progress_repo = FakeProgressRepository()
        student = make_student(student_repo)
        problem = make_problem(curriculum_repo)
        use_case = UpdateProblemProgressUseCase(
            student_repository=student_repo,
            curriculum_repository=curriculum_repo,
            progress_repository=progress_repo,
            event_publisher=FakeEventPublisher(),
        )

        result = use_case.execute(UpdateProblemProgressCommand(
            student_id=student.id,
            problem_id=problem.id,
            solved=True,
        ))

        assert result.solved_at is not None

    def test_nonexistent_student_raises_error(self):
        """Updating progress for nonexistent student raises error."""
        curriculum_repo = FakeCurriculumRepository()
        problem = make_problem(curriculum_repo)
        use_case = UpdateProblemProgressUseCase(
            student_repository=FakeStudentRepository(),
            curriculum_repository=curriculum_repo,
            progress_repository=FakeProgressRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(StudentNotFoundError):
            use_case.execute(UpdateProblemProgressCommand(
                student_id=uuid4(),
                problem_id=problem.id,
                solved=True,
            ))

    def test_nonexistent_problem_raises_error(self):
        """Updating progress for nonexistent problem raises error."""
        student_repo = FakeStudentRepository()
        student = make_student(student_repo)
        use_case = UpdateProblemProgressUseCase(
            student_repository=student_repo,
            curriculum_repository=FakeCurriculumRepository(),
            progress_repository=FakeProgressRepository(),
            event_publisher=FakeEventPublisher(),
        )

        with pytest.raises(ProblemNotFoundError):
            use_case.execute(UpdateProblemProgressCommand(
                student_id=student.id,
                problem_id=uuid4(),
                solved=True,
            ))