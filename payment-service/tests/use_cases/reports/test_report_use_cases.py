import pytest
from uuid import uuid4
from domain.enums import StudentPaymentStatus, TeacherPaymentStatus
from domain.models import StudentPayment, TeacherPayment
from application.use_cases.reports.get_payment_summary import (
    GetPaymentSummaryUseCase,
    GetPaymentSummaryCommand,
)
from application.use_cases.reports.get_student_payment_report import (
    GetStudentPaymentReportUseCase,
    GetStudentPaymentReportCommand,
)
from application.use_cases.reports.get_teacher_payment_report import (
    GetTeacherPaymentReportUseCase,
    GetTeacherPaymentReportCommand,
)
from tests.fakes import (
    FakeStudentPaymentRepository,
    FakeTeacherPaymentRepository,
)
from datetime import date


# ── Helpers ───────────────────────────────────────────────────────────────
def make_student_payment(
    repo: FakeStudentPaymentRepository,
    **overrides,
) -> StudentPayment:
    defaults = {
        "id": uuid4(),
        "student_id": uuid4(),
        "payment_month": "2025-06",
        "amount": 500.0,
        "currency": "ETB",
        "status": StudentPaymentStatus.PENDING,
        "reference_number": None,
        "note": None,
        "verified_by": None,
        "verified_at": None,
        "due_date": date(2025, 6, 30),
    }
    defaults.update(overrides)
    payment = StudentPayment(**defaults)
    repo.save(payment)
    return payment


def make_teacher_payment(
    repo: FakeTeacherPaymentRepository,
    **overrides,
) -> TeacherPayment:
    defaults = {
        "id": uuid4(),
        "teacher_id": uuid4(),
        "payment_month": "2025-06",
        "amount": 3000.0,
        "currency": "ETB",
        "status": TeacherPaymentStatus.PENDING,
        "note": None,
        "processed_by": None,
        "processed_at": None,
    }
    defaults.update(overrides)
    payment = TeacherPayment(**defaults)
    repo.save(payment)
    return payment


# ── GetPaymentSummary Tests ──────────────────────────────────────────────
class TestGetPaymentSummary:
    def test_counts_paid_student_payments(self):
        """Summary correctly counts paid student payments."""
        student_repo = FakeStudentPaymentRepository()
        teacher_repo = FakeTeacherPaymentRepository()

        make_student_payment(
            student_repo, status=StudentPaymentStatus.PAID, amount=500.0
        )
        make_student_payment(
            student_repo, status=StudentPaymentStatus.PAID, amount=500.0
        )
        make_student_payment(
            student_repo, status=StudentPaymentStatus.PENDING
        )

        use_case = GetPaymentSummaryUseCase(
            student_payment_repository=student_repo,
            teacher_payment_repository=teacher_repo,
        )

        result = use_case.execute(GetPaymentSummaryCommand(month="2025-06"))

        assert result.student_payments.total_paid == 2
        assert result.student_payments.total_pending == 1

    def test_calculates_total_amount_collected(self):
        """Summary correctly sums up total amount collected."""
        student_repo = FakeStudentPaymentRepository()
        teacher_repo = FakeTeacherPaymentRepository()

        make_student_payment(
            student_repo, status=StudentPaymentStatus.PAID, amount=500.0
        )
        make_student_payment(
            student_repo, status=StudentPaymentStatus.PAID, amount=500.0
        )

        use_case = GetPaymentSummaryUseCase(
            student_payment_repository=student_repo,
            teacher_payment_repository=teacher_repo,
        )

        result = use_case.execute(GetPaymentSummaryCommand(month="2025-06"))

        assert result.student_payments.total_amount_collected == 1000.0

    def test_counts_overdue_student_payments(self):
        """Summary correctly counts overdue student payments."""
        student_repo = FakeStudentPaymentRepository()
        teacher_repo = FakeTeacherPaymentRepository()

        make_student_payment(
            student_repo, status=StudentPaymentStatus.OVERDUE
        )
        make_student_payment(
            student_repo, status=StudentPaymentStatus.OVERDUE
        )

        use_case = GetPaymentSummaryUseCase(
            student_payment_repository=student_repo,
            teacher_payment_repository=teacher_repo,
        )

        result = use_case.execute(GetPaymentSummaryCommand(month="2025-06"))

        assert result.student_payments.total_overdue == 2

    def test_counts_paid_teacher_payments(self):
        """Summary correctly counts paid teacher payments."""
        student_repo = FakeStudentPaymentRepository()
        teacher_repo = FakeTeacherPaymentRepository()

        make_teacher_payment(
            teacher_repo, status=TeacherPaymentStatus.PAID, amount=3000.0
        )
        make_teacher_payment(
            teacher_repo, status=TeacherPaymentStatus.PENDING, amount=3000.0
        )

        use_case = GetPaymentSummaryUseCase(
            student_payment_repository=student_repo,
            teacher_payment_repository=teacher_repo,
        )

        result = use_case.execute(GetPaymentSummaryCommand(month="2025-06"))

        assert result.teacher_payments.total_paid == 1
        assert result.teacher_payments.total_pending == 1

    def test_calculates_teacher_amount_paid_and_pending(self):
        """Summary correctly sums teacher amounts."""
        student_repo = FakeStudentPaymentRepository()
        teacher_repo = FakeTeacherPaymentRepository()

        make_teacher_payment(
            teacher_repo, status=TeacherPaymentStatus.PAID, amount=3000.0
        )
        make_teacher_payment(
            teacher_repo, status=TeacherPaymentStatus.PENDING, amount=3000.0
        )

        use_case = GetPaymentSummaryUseCase(
            student_payment_repository=student_repo,
            teacher_payment_repository=teacher_repo,
        )

        result = use_case.execute(GetPaymentSummaryCommand(month="2025-06"))

        assert result.teacher_payments.total_amount_paid == 3000.0
        assert result.teacher_payments.total_amount_pending == 3000.0

    def test_empty_summary_when_no_payments(self):
        """Summary returns zeros when no payments exist."""
        use_case = GetPaymentSummaryUseCase(
            student_payment_repository=FakeStudentPaymentRepository(),
            teacher_payment_repository=FakeTeacherPaymentRepository(),
        )

        result = use_case.execute(GetPaymentSummaryCommand(month="2025-06"))

        assert result.student_payments.total_paid == 0
        assert result.student_payments.total_amount_collected == 0.0
        assert result.teacher_payments.total_paid == 0


# ── GetStudentPaymentReport Tests ────────────────────────────────────────
class TestGetStudentPaymentReport:
    def test_returns_all_payments_when_no_filter(self):
        """Returns all student payments when no filter provided."""
        repo = FakeStudentPaymentRepository()

        make_student_payment(repo, status=StudentPaymentStatus.PAID)
        make_student_payment(repo, status=StudentPaymentStatus.PENDING)
        make_student_payment(repo, status=StudentPaymentStatus.OVERDUE)

        use_case = GetStudentPaymentReportUseCase(
            student_payment_repository=repo,
        )

        result = use_case.execute(GetStudentPaymentReportCommand())

        assert len(result.payments) == 3

    def test_filters_by_status(self):
        """Filters report by payment status."""
        repo = FakeStudentPaymentRepository()

        make_student_payment(repo, status=StudentPaymentStatus.PAID)
        make_student_payment(repo, status=StudentPaymentStatus.PAID)
        make_student_payment(repo, status=StudentPaymentStatus.PENDING)

        use_case = GetStudentPaymentReportUseCase(
            student_payment_repository=repo,
        )

        result = use_case.execute(
            GetStudentPaymentReportCommand(
                status=StudentPaymentStatus.PAID,
            )
        )

        assert len(result.payments) == 2
        assert all(
            p.status == StudentPaymentStatus.PAID for p in result.payments
        )

    def test_returns_cohort_id_in_result(self):
        """Result carries cohort_id filter for context."""
        repo = FakeStudentPaymentRepository()
        cohort_id = uuid4()

        use_case = GetStudentPaymentReportUseCase(
            student_payment_repository=repo,
        )

        result = use_case.execute(
            GetStudentPaymentReportCommand(
                cohort_id=cohort_id,
            )
        )

        assert result.cohort_id == cohort_id

    def test_returns_month_in_result(self):
        """Result carries month filter for context."""
        repo = FakeStudentPaymentRepository()

        use_case = GetStudentPaymentReportUseCase(
            student_payment_repository=repo,
        )

        result = use_case.execute(
            GetStudentPaymentReportCommand(
                month="2025-06",
            )
        )

        assert result.month == "2025-06"


# ── GetTeacherPaymentReport Tests ────────────────────────────────────────
class TestGetTeacherPaymentReport:
    def test_returns_all_payments_when_no_filter(self):
        """Returns all teacher payments when no filter provided."""
        repo = FakeTeacherPaymentRepository()

        make_teacher_payment(repo, status=TeacherPaymentStatus.PAID)
        make_teacher_payment(repo, status=TeacherPaymentStatus.PENDING)

        use_case = GetTeacherPaymentReportUseCase(
            teacher_payment_repository=repo,
        )

        result = use_case.execute(GetTeacherPaymentReportCommand())

        assert len(result.payments) == 2

    def test_filters_by_month(self):
        """Filters by payment month."""
        repo = FakeTeacherPaymentRepository()

        make_teacher_payment(repo, payment_month="2025-06")
        make_teacher_payment(repo, payment_month="2025-06")
        make_teacher_payment(repo, payment_month="2025-07")

        use_case = GetTeacherPaymentReportUseCase(
            teacher_payment_repository=repo,
        )

        result = use_case.execute(
            GetTeacherPaymentReportCommand(
                month="2025-06",
            )
        )

        assert len(result.payments) == 2
        assert all(p.payment_month == "2025-06" for p in result.payments)

    def test_filters_by_status(self):
        """Filters by payment status."""
        repo = FakeTeacherPaymentRepository()

        make_teacher_payment(repo, status=TeacherPaymentStatus.PAID)
        make_teacher_payment(repo, status=TeacherPaymentStatus.PENDING)
        make_teacher_payment(repo, status=TeacherPaymentStatus.PENDING)

        use_case = GetTeacherPaymentReportUseCase(
            teacher_payment_repository=repo,
        )

        result = use_case.execute(
            GetTeacherPaymentReportCommand(
                status=TeacherPaymentStatus.PENDING,
            )
        )

        assert len(result.payments) == 2
        assert all(
            p.status == TeacherPaymentStatus.PENDING for p in result.payments
        )

    def test_returns_month_in_result(self):
        """Result carries month filter for context."""
        repo = FakeTeacherPaymentRepository()

        use_case = GetTeacherPaymentReportUseCase(
            teacher_payment_repository=repo,
        )

        result = use_case.execute(
            GetTeacherPaymentReportCommand(
                month="2025-06",
            )
        )

        assert result.month == "2025-06"