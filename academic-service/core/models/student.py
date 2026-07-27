import uuid

from django.db import models

from core.models.choices import StudentStatusChoices, YEAR_PHASE_CHOICES
from core.models.cohort import Cohort
from core.models.teacher import Teacher


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True)  # links to Auth Service
    full_name = models.CharField(max_length=150)
    email = models.EmailField()  # denormalized from Auth for display
    cohort = models.ForeignKey(
        Cohort, null=True, blank=True, on_delete=models.SET_NULL, related_name="students"
    )
    year_phase = models.IntegerField(choices=YEAR_PHASE_CHOICES, default=1)
    status = models.CharField(
        max_length=20,
        choices=StudentStatusChoices.choices,
        default=StudentStatusChoices.ACTIVE,
    )
    assigned_teacher = models.ForeignKey(
        Teacher, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_students"
    )
    attendance_percentage = models.FloatField(default=0.0)
    active_warning_count = models.IntegerField(default=0)
    joined_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student"

    def __str__(self):
        return f"{self.full_name} ({self.status})"