from rest_framework import serializers
from domain.enums import StudentPaymentStatus, TeacherPaymentStatus


# ── Request Serializers ───────────────────────────────────────────────────

class RecordStudentPaymentSerializer(serializers.Serializer):
    paymentMonth = serializers.RegexField(
        regex=r'^\d{4}-(0[1-9]|1[0-2])$',
        error_messages={"invalid": "paymentMonth must be in YYYY-MM format"},
    )
    amount = serializers.FloatField(min_value=0)
    currency = serializers.CharField(max_length=10)
    dueDate = serializers.DateField()
    referenceNumber = serializers.CharField(
        max_length=200, required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_null=True)


class SubmitPaymentReferenceSerializer(serializers.Serializer):
    paymentMonth = serializers.RegexField(
        regex=r'^\d{4}-(0[1-9]|1[0-2])$',
    )
    referenceNumber = serializers.CharField(
        min_length=3, max_length=200
    )
    amount = serializers.FloatField(min_value=0)
    currency = serializers.CharField(max_length=10)
    dueDate = serializers.DateField()
    note = serializers.CharField(required=False, allow_null=True)


class UpdateStudentPaymentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["PAID", "FAILED", "OVERDUE"]
    )
    note = serializers.CharField(required=False, allow_null=True)


class RecordTeacherPaymentSerializer(serializers.Serializer):
    paymentMonth = serializers.RegexField(
        regex=r'^\d{4}-(0[1-9]|1[0-2])$',
    )
    amount = serializers.FloatField(min_value=0)
    currency = serializers.CharField(max_length=10)
    note = serializers.CharField(required=False, allow_null=True)


class UpdateTeacherPaymentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["PAID", "CANCELLED"])
    note = serializers.CharField(required=False, allow_null=True)


# ── Response Serializers ──────────────────────────────────────────────────

class StudentPaymentResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    studentId = serializers.UUIDField(source="student_id")
    paymentMonth = serializers.CharField(source="payment_month")
    amount = serializers.FloatField()
    currency = serializers.CharField()
    status = serializers.SerializerMethodField()
    referenceNumber = serializers.CharField(
        source="reference_number", allow_null=True
    )
    note = serializers.CharField(allow_null=True)
    verifiedBy = serializers.UUIDField(
        source="verified_by", allow_null=True
    )
    verifiedAt = serializers.DateTimeField(
        source="verified_at", allow_null=True
    )
    dueDate = serializers.DateField(source="due_date")
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")

    def get_status(self, obj):
        # Extract status property dynamically from dict or object safely
        status_val = getattr(obj, 'status', None) or (obj.get('status') if isinstance(obj, dict) else None)
        if hasattr(status_val, 'value'):
            return status_val.value
        return str(status_val) if status_val is not None else None

class TeacherPaymentResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    teacherId = serializers.UUIDField(source="teacher_id")
    paymentMonth = serializers.CharField(source="payment_month")
    amount = serializers.FloatField()
    currency = serializers.CharField()
    status = serializers.SerializerMethodField()
    note = serializers.CharField(allow_null=True)
    processedBy = serializers.UUIDField(
        source="processed_by", allow_null=True
    )
    processedAt = serializers.DateTimeField(
        source="processed_at", allow_null=True
    )
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")
    
    def get_status(self, obj):
        status_val = getattr(obj, 'status', None) or (obj.get('status') if isinstance(obj, dict) else None)
        if hasattr(status_val, 'value'):
            return status_val.value
        return str(status_val) if status_val is not None else None

class SubscriptionStatusResponseSerializer(serializers.Serializer):
    studentId = serializers.UUIDField(source="student_id")
    subscriptionStatus = serializers.CharField(
        source="subscription_status"
    )
    currentMonthPaid = serializers.BooleanField(
        source="current_month_paid"
    )
    nextDueDate = serializers.DateField(
        source="next_due_date", allow_null=True
    )
    lastPaymentDate = serializers.DateField(
        source="last_payment_date", allow_null=True
    )
    lastPaymentAmount = serializers.FloatField(
        source="last_payment_amount", allow_null=True
    )