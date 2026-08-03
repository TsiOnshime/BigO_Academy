"""
domain/models.py — Payment Service

Domain models (plain dataclasses, no framework/ORM dependency).

StudentPayment — a single month's payment record for a student's
subscription. Created either by an admin recording a payment
(RecordStudentPaymentUseCase) or by a student submitting a payment
reference for admin verification (SubmitPaymentReferenceUseCase).

TeacherPayment — a single month's payout record for a teacher.
Created by an admin (RecordTeacherPaymentUseCase) and moved through
its lifecycle by UpdateTeacherPaymentStatusUseCase.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from domain.enums import StudentPaymentStatus, TeacherPaymentStatus

# ── Status transition tables ────────────────────────────────────────────────

_STUDENT_PAYMENT_TRANSITIONS: dict[StudentPaymentStatus, set[StudentPaymentStatus]] = {
    StudentPaymentStatus.PENDING: {
        StudentPaymentStatus.PAID,
        StudentPaymentStatus.FAILED,
        StudentPaymentStatus.OVERDUE,
    },
    StudentPaymentStatus.OVERDUE: {
        StudentPaymentStatus.PAID,
        StudentPaymentStatus.FAILED,
    },
    StudentPaymentStatus.PAID: set(),
    StudentPaymentStatus.FAILED: set(),
}

_TEACHER_PAYMENT_TRANSITIONS: dict[TeacherPaymentStatus, set[TeacherPaymentStatus]] = {
    TeacherPaymentStatus.PENDING: {
        TeacherPaymentStatus.PAID,
        TeacherPaymentStatus.CANCELLED,
        TeacherPaymentStatus.FAILED,
    },
    TeacherPaymentStatus.PAID: set(),
    TeacherPaymentStatus.CANCELLED: set(),
    TeacherPaymentStatus.FAILED: set(),
}


# ── Models ───────────────────────────────────────────────────────────────


@dataclass
class StudentPayment:
    id: UUID
    student_id: UUID
    payment_month: str  # "YYYY-MM"
    amount: float
    currency: str
    status: StudentPaymentStatus
    due_date: date
    reference_number: Optional[str] = None
    note: Optional[str] = None
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    cohort_id: Optional[UUID] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_paid(self) -> bool:
        return self.status == StudentPaymentStatus.PAID

    def can_transition_to(self, target_status: StudentPaymentStatus) -> bool:
        return target_status in _STUDENT_PAYMENT_TRANSITIONS.get(
            self.status, set()
        )


@dataclass
class TeacherPayment:
    id: UUID
    teacher_id: UUID
    payment_month: str  # "YYYY-MM"
    amount: float
    currency: str
    status: TeacherPaymentStatus
    note: Optional[str] = None
    processed_by: Optional[UUID] = None
    processed_at: Optional[datetime] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_paid(self) -> bool:
        return self.status == TeacherPaymentStatus.PAID

    def can_transition_to(self, target_status: TeacherPaymentStatus) -> bool:
        return target_status in _TEACHER_PAYMENT_TRANSITIONS.get(
            self.status, set()
        )