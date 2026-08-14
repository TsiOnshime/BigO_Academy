import uuid

from django.db import models

from core.models.choices import MentorshipSessionStatusChoices
from core.models.student import Student
from core.models.teacher import Teacher


class MentorshipSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="mentorship_sessions")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="mentorship_sessions")
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=MentorshipSessionStatusChoices.choices,
        default=MentorshipSessionStatusChoices.SCHEDULED,
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = "mentorship_session"

    def __str__(self):
        return f"{self.teacher_id} / {self.student_id} @ {self.scheduled_at}"