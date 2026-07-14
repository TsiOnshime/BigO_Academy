import uuid

from django.db import models

from core.models.choices import TeacherStatusChoices


class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True)  # links to Auth Service
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=TeacherStatusChoices.choices,
        default=TeacherStatusChoices.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teacher"

    def __str__(self):
        return f"{self.full_name} ({self.status})"