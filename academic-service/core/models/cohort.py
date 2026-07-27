import uuid

from django.db import models

from core.models.choices import CohortStatusChoices
from core.models.teacher import Teacher


class Cohort(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=CohortStatusChoices.choices,
        default=CohortStatusChoices.ACTIVE,
    )
    intake_window_one = models.DateField(null=True, blank=True)
    intake_window_two = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    expected_graduation_date = models.DateField()
    student_capacity = models.IntegerField()
    # Denormalized counters — domain.Cohort.enrolled_student_count / teacher_count.
    # Kept in sync by the CohortRepository adapter on assign/unassign.
    enrolled_student_count = models.IntegerField(default=0)
    teacher_count = models.IntegerField(default=0)
    teachers = models.ManyToManyField(Teacher, blank=True, related_name="cohorts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cohort"

    def __str__(self):
        return self.name