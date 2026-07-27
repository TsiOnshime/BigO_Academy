import uuid

from django.db import models

from core.models.choices import WarningStatusChoices, WarningTypeChoices
from core.models.student import Student


class Warning(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="warnings")
    type = models.CharField(max_length=40, choices=WarningTypeChoices.choices)
    status = models.CharField(
        max_length=20,
        choices=WarningStatusChoices.choices,
        default=WarningStatusChoices.ACTIVE,
    )
    warning_number = models.IntegerField()  # 1, 2, or 3
    issued_at = models.DateTimeField(auto_now_add=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    dismissed_by = models.UUIDField(null=True, blank=True)
    dismissal_note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "warning"

    def __str__(self):
        return f"{self.student_id}: {self.type} #{self.warning_number} ({self.status})"