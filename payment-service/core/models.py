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
    
    def __str__(self):
        return f"TeacherPayment({self.teacher_id}, {self.payment_month}, {self.status})"
    