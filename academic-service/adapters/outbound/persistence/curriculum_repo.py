"""
Note on naming: domain.Topic.curriculum_id is literally the owning
Cohort's id (one curriculum per cohort — see create_topic.py use case).
The ORM field is named `cohort` for clarity; this repo translates
cohort_id <-> curriculum_id at the mapping boundary.

Topic.problem_count is a denormalized counter, kept in sync here whenever
a Problem under that topic is created or deleted.
"""
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.db.models import F

from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort
from core.models import Problem as ProblemORM
from core.models import Topic as TopicORM
from domain.enums import ProblemDifficulty, ProblemSource, YearPhase
from domain.models import Problem, Topic


class DjangoCurriculumRepository(CurriculumRepositoryPort):

    # ── Topics ──────────────────────────────────────────────────────────

    def save_topic(self, topic: Topic) -> Topic:
        orm, _ = TopicORM.objects.update_or_create(
            id=topic.id,
            defaults={
                "cohort_id": topic.curriculum_id,
                "title": topic.title,
                "description": topic.description,
                "year_phase": topic.year_phase.value if hasattr(topic.year_phase, "value") else int(topic.year_phase),
                "display_order": topic.display_order,
                "problem_count": topic.problem_count,
            },
        )
        return self._topic_to_domain(orm)

    def find_topic_by_id(self, topic_id: UUID) -> Optional[Topic]:
        try:
            orm = TopicORM.objects.get(id=topic_id)
        except TopicORM.DoesNotExist:
            return None
        return self._topic_to_domain(orm)

    def find_topics_by_cohort(
        self, cohort_id: UUID, year_phase: Optional[YearPhase] = None
    ) -> list[Topic]:
        queryset = TopicORM.objects.filter(cohort_id=cohort_id)
        if year_phase is not None:
            yp_val = year_phase.value if hasattr(year_phase, "value") else int(year_phase)
            queryset = queryset.filter(year_phase=yp_val)
        queryset = queryset.order_by("display_order")
        return [self._topic_to_domain(orm) for orm in queryset]

    def delete_topic(self, topic_id: UUID) -> None:
        TopicORM.objects.filter(id=topic_id).delete()

    def reorder_topics(self, ordered_topic_ids: list[UUID]) -> None:
        with transaction.atomic():
            for index, topic_id in enumerate(ordered_topic_ids):
                TopicORM.objects.filter(id=topic_id).update(display_order=index)

    # ── Problems ────────────────────────────────────────────────────────

    def save_problem(self, problem: Problem) -> Problem:
        with transaction.atomic():
            is_new = not ProblemORM.objects.filter(id=problem.id).exists()
            source_val = problem.source.value if hasattr(problem.source, "value") else str(problem.source)
            diff_val = problem.difficulty.value if hasattr(problem.difficulty, "value") else str(problem.difficulty)
            orm, _ = ProblemORM.objects.update_or_create(
                id=problem.id,
                defaults={
                    "topic_id": problem.topic_id,
                    "title": problem.title,
                    "source": source_val,
                    "external_url": problem.external_url,
                    "difficulty": diff_val,
                },
            )
            if is_new:
                TopicORM.objects.filter(id=problem.topic_id).update(
                    problem_count=F("problem_count") + 1
                )
        return self._problem_to_domain(orm)


    def find_problem_by_id(self, problem_id: UUID) -> Optional[Problem]:
        try:
            orm = ProblemORM.objects.get(id=problem_id)
        except ProblemORM.DoesNotExist:
            return None
        return self._problem_to_domain(orm)

    def find_problems_by_topic(self, topic_id: UUID) -> list[Problem]:
        queryset = ProblemORM.objects.filter(topic_id=topic_id)
        return [self._problem_to_domain(orm) for orm in queryset]

    def delete_problem(self, problem_id: UUID) -> None:
        with transaction.atomic():
            try:
                orm = ProblemORM.objects.get(id=problem_id)
            except ProblemORM.DoesNotExist:
                return
            topic_id = orm.topic_id
            orm.delete()
            TopicORM.objects.filter(id=topic_id).update(
                problem_count=F("problem_count") - 1
            )

    # ── Mapping ─────────────────────────────────────────────────────────

    def _topic_to_domain(self, orm: TopicORM) -> Topic:
        return Topic(
            id=orm.id,
            curriculum_id=orm.cohort_id,
            title=orm.title,
            description=orm.description,
            year_phase=YearPhase(orm.year_phase),
            display_order=orm.display_order,
            problem_count=orm.problem_count,
            created_at=orm.created_at,
        )

    def _problem_to_domain(self, orm: ProblemORM) -> Problem:
        return Problem(
            id=orm.id,
            topic_id=orm.topic_id,
            title=orm.title,
            source=ProblemSource(orm.source),
            external_url=orm.external_url,
            difficulty=ProblemDifficulty(orm.difficulty),
            created_at=orm.created_at,
        )