import uuid

from django.db import models

from core.models.choices import ContestStatusChoices
from core.models.cohort import Cohort
from core.models.student import Student


class Contest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="contests")
    external_contest_url = models.URLField()
    status = models.CharField(
        max_length=20,
        choices=ContestStatusChoices.choices,
        default=ContestStatusChoices.UPCOMING,
    )
    scheduled_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    problem_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contest"

    def __str__(self):
        return self.title


class ContestResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="contest_results")
    # Denormalized snapshot of the student's name at result-submission time,
    # per domain.ContestResult.student_name.
    student_name = models.CharField(max_length=150)
    contest_rank = models.IntegerField()
    problems_solved = models.IntegerField(default=0)
    participated = models.BooleanField(default=True)

    class Meta:
        db_table = "contest_result"
        unique_together = [["contest", "student"]]

    def __str__(self):
        return f"{self.student_name} @ {self.contest_id}: rank {self.contest_rank}"