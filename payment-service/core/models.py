import uuid 
from django.db import models


class StudentPaymentModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student_id = models.UUIDField(db_index=True)
    cohort_id = models.UUIDField(null=True, blank=True, db_index=True)
    payment_month = models.CharField(max_length=7)
    amount= models.FloatField()
    currency = models.CharField(max_length=10, default="ETB")
    status = models.CharField(max_length=20)
    reference_number = models.CharField(
        max_length=200, null=True, blank=True
    )
    note = models.TextField(null=True, blank=True)
    verified_by = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "student_payment"
        unique_together = [("student_id", "payment_month")]
        ordering = ["-created_at"]
        indexes = [
            # Payment history per student — most common query
            models.Index(
                fields=["student_id", "-created_at"],
                name="idx_student_payment_history",
            ),
            # Status filter — pending verification, overdue lists
            models.Index(
                fields=["status", "-created_at"],
                name="idx_student_payment_status",
            ),
            # Due date filter — overdue job queries
            models.Index(
                fields=["status", "due_date"],
                name="idx_student_payment_due",
            ),
            # Cohort + status — admin cohort payment reports
            models.Index(
                fields=["cohort_id", "status"],
                name="idx_student_payment_cohort_status",
            ),
        ]
    
    def __str__(self):
        return f"StudentPayment({self.student_id}, {self.payment_month}, {self.status})"
    
class TeacherPaymentModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    teacher_id = models.UUIDField(db_index=True)
    payment_month = models.CharField(max_length = 7)
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default="ETB")
    status = models.CharField(max_length=20)
    note = models.TextField(null=True, blank=True)
    processed_by = models.UUIDField(null=True, blank=True)
    processed_at = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        db_table = "teacher_payment"
        ordering = ["-created_at"]
        indexes = [
            # Payment history per teacher
            models.Index(
                fields=["teacher_id", "-created_at"],
                name="idx_teacher_payment_history",
            ),
            # Status filter — pending teacher payments
            models.Index(
                fields=["status", "-created_at"],
                name="idx_teacher_payment_status",
            ),
            # Monthly report queries
            models.Index(
                fields=["payment_month"],
                name="idx_teacher_payment_month",
            ),
        ]
    
    def __str__(self):
        return f"TeacherPayment({self.teacher_id}, {self.payment_month}, {self.status})"
    