from enum import Enum


class BillingCycle(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    VOID = "VOID"


class TransactionType(str, Enum):
    STUDENT_PAYMENT = "STUDENT_PAYMENT"
    TEACHER_PAYOUT = "TEACHER_PAYOUT"
    REFUND = "REFUND"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class PayoutRateType(str, Enum):
    PER_SESSION = "PER_SESSION"
    MONTHLY_SALARY = "MONTHLY_SALARY"
    PER_STUDENT = "PER_STUDENT"


class PayoutStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    FAILED = "FAILED"