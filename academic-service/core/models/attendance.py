import uuid

from django.db import models

from core.models.choices import AttendanceStatusChoices
from core.models.cohort import Cohort
from core.models.student import Student


class ClassSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="class_sessions")
    session_date = models.DateField()
    total_students = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    excused_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "class_session"

    def __str__(self):
        return f"{self.cohort_id} @ {self.session_date}"


class AttendanceRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ClassSession, on_delete=models.CASCADE, related_name="attendance_records"
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=AttendanceStatusChoices.choices)
    note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "attendance_record"
        unique_together = [["session", "student"]]

    def __str__(self):
        return f"{self.student_id} @ {self.session_id}: {self.status}"