import uuid

from django.db import models

from core.models.curriculum import Problem
from core.models.student import Student


class ProblemProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="progress_records")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="progress_records")
    solved = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)
    solve_time_minutes = models.IntegerField(default=0)
    verified_by_teacher = models.BooleanField(default=False)
    solved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "problem_progress"
        unique_together = [["student", "problem"]]

    def __str__(self):
        return f"{self.student_id} / {self.problem_id} solved={self.solved}"