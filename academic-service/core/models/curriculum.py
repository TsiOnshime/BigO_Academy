import uuid

from django.db import models

from core.models.choices import (
    ProblemDifficultyChoices,
    ProblemSourceChoices,
    YEAR_PHASE_CHOICES,
)
from core.models.cohort import Cohort


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # domain.Topic.curriculum_id — in this domain, a cohort has exactly one
    # curriculum, so curriculum_id is literally the owning Cohort's id.
    # Named `cohort` here for ORM clarity; mapped to/from curriculum_id in
    # the repository adapter.
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    year_phase = models.IntegerField(choices=YEAR_PHASE_CHOICES)
    display_order = models.IntegerField(default=0)
    # domain.Topic.problem_count — denormalized count, kept in sync by the
    # CurriculumRepository adapter whenever a Problem is added/removed.
    problem_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "topic"
        ordering = ["display_order"]

    def __str__(self):
        return self.title


class Problem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="problems")
    title = models.CharField(max_length=200)
    source = models.CharField(max_length=20, choices=ProblemSourceChoices.choices)
    external_url = models.URLField()
    difficulty = models.CharField(max_length=10, choices=ProblemDifficultyChoices.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "problem"

    def __str__(self):
        return self.title