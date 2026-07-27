class DomainError(Exception):
    """Base class for all domain-level errors in the Payment Service."""

    pass


# ── Not Found Errors ───────────────────────────────────────────────────────


class SubscriptionPlanNotFoundError(DomainError):
    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        super().__init__(f"Subscription plan not found: {plan_id}")


class SubscriptionNotFoundError(DomainError):
    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        super().__init__(f"Subscription not found: {subscription_id}")


class InvoiceNotFoundError(DomainError):
    def __init__(self, invoice_id: str):
        self.invoice_id = invoice_id
        super().__init__(f"Invoice not found: {invoice_id}")


class TransactionNotFoundError(DomainError):
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        super().__init__(f"Transaction not found: {transaction_id}")


class TeacherPayoutRateNotFoundError(DomainError):
    def __init__(self, teacher_id: str):
        self.teacher_id = teacher_id
        super().__init__(f"No payout rate configured for teacher: {teacher_id}")


class TeacherPayoutNotFoundError(DomainError):
    def __init__(self, payout_id: str):
        self.payout_id = payout_id
        super().__init__(f"Teacher payout not found: {payout_id}")


class StudentPaymentNotFoundError(DomainError):
    def __init__(self, payment_id: str):
        self.payment_id = payment_id
        super().__init__(f"Student payment not found: {payment_id}")


class TeacherPaymentNotFoundError(DomainError):
    def __init__(self, payment_id: str):
        self.payment_id = payment_id
        super().__init__(f"Teacher payment not found: {payment_id}")


# ── Conflict Errors ─────────────────────────────────────────────────────────


class StudentAlreadySubscribedError(DomainError):
    """Raised when subscribing a student to a plan they already have an
    active subscription to."""

    def __init__(self, student_id: str, plan_id: str):
        self.student_id = student_id
        self.plan_id = plan_id
        super().__init__(
            f"Student {student_id} already has an active subscription to plan {plan_id}"
        )


class InvoiceAlreadyPaidError(DomainError):
    """Raised when trying to mark an already-paid invoice as paid again,
    or void a paid invoice."""

    def __init__(self, invoice_id: str):
        self.invoice_id = invoice_id
        super().__init__(f"Invoice {invoice_id} has already been paid")


class PayoutAlreadyProcessedError(DomainError):
    """Raised when trying to approve or pay a payout that's already PAID."""

    def __init__(self, payout_id: str):
        self.payout_id = payout_id
        super().__init__(f"Payout {payout_id} has already been processed")


class DuplicatePaymentError(DomainError):
    """Raised when a student payment (or reference submission) already
    exists for the given student and payment month."""

    def __init__(self, student_id: str, payment_month: str):
        self.student_id = student_id
        self.payment_month = payment_month
        super().__init__(
            f"Payment already recorded for student {student_id}, month {payment_month}"
        )


class PayoutPeriodAlreadyComputedError(DomainError):
    """Raised when computing a payout for a teacher/period pair that
    already has a payout on record."""

    def __init__(self, teacher_id: str, period_start: str, period_end: str):
        self.teacher_id = teacher_id
        self.period_start = period_start
        self.period_end = period_end
        super().__init__(
            f"Payout already computed for teacher {teacher_id}, "
            f"period {period_start} to {period_end}"
        )


# ── Invalid State Transition Errors ─────────────────────────────────────────


class InvalidSubscriptionStatusTransitionError(DomainError):
    """
    Raised when attempting an invalid subscription status transition.
    Valid transitions:
    ACTIVE → PAST_DUE
    ACTIVE → CANCELLED
    PAST_DUE → ACTIVE (payment recovered)
    PAST_DUE → CANCELLED
    ACTIVE / PAST_DUE → EXPIRED (period ended, not renewed)
    """

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid subscription status transition: {current_status} → {target_status}"
        )


class InvalidInvoiceStatusTransitionError(DomainError):
    """
    Raised when attempting an invalid invoice status transition.
    Valid transitions:
    DRAFT → ISSUED
    DRAFT → VOID
    ISSUED → PAID
    ISSUED → OVERDUE
    ISSUED → VOID
    OVERDUE → PAID
    OVERDUE → VOID
    """

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid invoice status transition: {current_status} → {target_status}"
        )


class InvalidPayoutStatusTransitionError(DomainError):
    """
    Raised when attempting an invalid teacher payout status transition.
    Valid transitions:
    PENDING → APPROVED
    PENDING → FAILED
    APPROVED → PAID
    APPROVED → FAILED
    """

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid payout status transition: {current_status} → {target_status}"
        )


class InvalidPaymentStatusTransitionError(DomainError):
    """
    Raised when attempting an invalid status transition on a student or
    teacher payment record.

    Valid StudentPayment transitions:
    PENDING → PAID
    PENDING → FAILED
    PENDING → OVERDUE
    OVERDUE → PAID
    OVERDUE → FAILED

    Valid TeacherPayment transitions:
    PENDING → PAID
    PENDING → CANCELLED
    PENDING → FAILED
    """

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid payment status transition: {current_status} → {target_status}"
        )


class SubscriptionNotActiveError(DomainError):
    """Raised when trying to perform an operation (e.g. issuing an
    invoice) against a subscription that isn't ACTIVE."""

    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        super().__init__(f"Subscription {subscription_id} is not active")


class InvoiceNotIssuedError(DomainError):
    """Raised when trying to mark an invoice as paid/overdue before it's
    been issued (still DRAFT)."""

    def __init__(self, invoice_id: str):
        self.invoice_id = invoice_id
        super().__init__(f"Invoice {invoice_id} has not been issued yet")


class PayoutNotApprovedError(DomainError):
    """Raised when trying to mark a payout as PAID before it's been
    APPROVED."""

    def __init__(self, payout_id: str):
        self.payout_id = payout_id
        super().__init__(f"Payout {payout_id} has not been approved yet")


# ── Validation Errors ────────────────────────────────────────────────────────


class InvalidAmountError(DomainError):
    """Raised when an amount is zero, negative, or otherwise invalid for
    the operation (invoice, transaction, payout, etc.)."""

    def __init__(self, amount, reason: str = "Amount must be greater than zero"):
        self.amount = amount
        self.reason = reason
        super().__init__(f"Invalid amount {amount}: {reason}")


class CurrencyMismatchError(DomainError):
    """Raised when two amounts that must share a currency don't —
    e.g. refunding a transaction in a different currency than it was
    charged in."""

    def __init__(self, expected_currency: str, actual_currency: str):
        self.expected_currency = expected_currency
        self.actual_currency = actual_currency
        super().__init__(
            f"Currency mismatch: expected {expected_currency}, got {actual_currency}"
        )


# ── Permission Errors ─────────────────────────────────────────────────────


class UnauthorizedAccessError(DomainError):
    """
    Raised when a user tries to access a resource they don't have
    permission for — e.g. a student accessing another student's invoices.
    """

    def __init__(self, reason: str = "You do not have permission to access this resource"):
        super().__init__(reason)