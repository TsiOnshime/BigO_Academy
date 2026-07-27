import pytest 
from uuid import uuid4 
from datetime import date, timedelta 
 
from domain.enums import StudentPaymentStatus 
from domain.exceptions import ( 
    DuplicatePaymentError, 
    StudentPaymentNotFoundError, 
    InvalidPaymentStatusTransitionError, 
) 
from domain.models import StudentPayment 
from application.use_cases.student_payment.record_student_payment import ( 
    RecordStudentPaymentUseCase, RecordStudentPaymentCommand, 
) 
from application.use_cases.student_payment.submit_payment_reference import ( 
    SubmitPaymentReferenceUseCase, SubmitPaymentReferenceCommand, 
) 
from application.use_cases.student_payment.get_student_payment_history import ( 
    GetStudentPaymentHistoryUseCase, GetStudentPaymentHistoryCommand, 
) 
from application.use_cases.student_payment.get_subscription_status import ( 
    GetSubscriptionStatusUseCase, GetSubscriptionStatusCommand, 
) 
from application.use_cases.student_payment.update_student_payment_status import ( 
    UpdateStudentPaymentStatusUseCase, UpdateStudentPaymentStatusCommand, 
) 
from application.use_cases.student_payment.list_overdue_students import ( 
    ListOverdueStudentsUseCase, ListOverdueStudentsCommand, 
) 
from application.use_cases.student_payment.list_pending_verification import ( 
    ListPendingVerificationUseCase, ListPendingVerificationCommand, 
) 
from tests.fakes import ( 
    FakeStudentPaymentRepository, 
    FakeEventPublisher, 
) 
 
 
# ── Helpers 

 
def make_payment( 
    repo: FakeStudentPaymentRepository, 
    student_id=None, 
    **overrides, 
) -> StudentPayment: 
    defaults = { 
        "id": uuid4(), 
        "student_id": student_id or uuid4(), 
        "payment_month": "2025-06", 
        "amount": 500.0, 
        "currency": "ETB", 
        "status": StudentPaymentStatus.PENDING, 
        "reference_number": "TXN-001", 
        "note": None, 
        "verified_by": None, 
        "verified_at": None, 
        "due_date": date(2025, 6, 30), 
    } 
    defaults.update(overrides) 
    payment = StudentPayment(**defaults) 
    repo.save(payment) 
    return payment 
 
 
# ── RecordStudentPayment Tests 
 
class TestRecordStudentPayment: 
 
    def test_records_payment_successfully(self): 
        """Happy path — admin records a student payment.""" 
        repo = FakeStudentPaymentRepository() 
        use_case = RecordStudentPaymentUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(RecordStudentPaymentCommand( 
            student_id=uuid4(), 
            payment_month="2025-06", 
            amount=500.0, 
            currency="ETB", 
            due_date=date(2025, 6, 30), 
        )) 
 
        assert result.payment.amount == 500.0 
        assert result.payment.currency == "ETB" 
        assert result.payment.payment_month == "2025-06" 
 
    def test_new_payment_starts_pending(self): 
        """Recorded payment starts as PENDING awaiting verification.""" 
        repo = FakeStudentPaymentRepository() 
        use_case = RecordStudentPaymentUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(RecordStudentPaymentCommand( 
            student_id=uuid4(), 
            payment_month="2025-06", 
            amount=500.0, 
            currency="ETB", 
            due_date=date(2025, 6, 30), 
        )) 
 
        assert result.payment.status == StudentPaymentStatus.PENDING 
 
    def test_publishes_payment_recorded_event(self): 
        """StudentPaymentRecorded event must be published.""" 
        repo = FakeStudentPaymentRepository() 
        event_publisher = FakeEventPublisher() 
        use_case = RecordStudentPaymentUseCase( 
            student_payment_repository=repo, 
            event_publisher=event_publisher, 
        ) 
 
        use_case.execute(RecordStudentPaymentCommand( 
            student_id=uuid4(), 
            payment_month="2025-06", 
            amount=500.0, 
            currency="ETB", 
            due_date=date(2025, 6, 30), 
        )) 
 
        events = event_publisher.get_events_of_type( 
            "student_payment_recorded" 
        ) 
        assert len(events) == 1 
 
    def test_duplicate_payment_raises_error(self): 
        """Cannot record two payments for same student and month.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        use_case = RecordStudentPaymentUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        use_case.execute(RecordStudentPaymentCommand( 
            student_id=student_id, 
            payment_month="2025-06", 
            amount=500.0, 
            currency="ETB", 
            due_date=date(2025, 6, 30), 
        )) 
 
        with pytest.raises(DuplicatePaymentError): 
            use_case.execute(RecordStudentPaymentCommand( 
                student_id=student_id, 
                payment_month="2025-06", 
                amount=500.0, 
                currency="ETB", 
                due_date=date(2025, 6, 30), 
            )) 
 
    def test_different_months_can_both_be_recorded(self): 
        """Same student can have payments for different months.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        use_case = RecordStudentPaymentUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        use_case.execute(RecordStudentPaymentCommand( 
            student_id=student_id, 
            payment_month="2025-06", 
            amount=500.0, 
            currency="ETB", 
            due_date=date(2025, 6, 30), 
        )) 
 
        # Different month — should succeed 
        result = use_case.execute(RecordStudentPaymentCommand( 
            student_id=student_id, 
            payment_month="2025-07", 
            amount=500.0, 
            currency="ETB", 
            due_date=date(2025, 7, 31), 
        )) 
 
        assert result.payment.payment_month == "2025-07" 
 
 
# ── SubmitPaymentReference Tests 
 
class TestSubmitPaymentReference: 
 
    def test_submits_reference_successfully(self): 
        """Student submits a reference — payment created as PENDING.""" 
        repo = FakeStudentPaymentRepository() 
        use_case = SubmitPaymentReferenceUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(SubmitPaymentReferenceCommand( 
            student_id=uuid4(), 
            payment_month="2025-06", 
            reference_number="TXN-2025-0612-ABC", 
            due_date=date(2025, 6, 30), 
            amount=500.0, 
            currency="ETB", 
        )) 
 
        assert result.payment.reference_number == "TXN-2025-0612-ABC" 
        assert result.payment.status == StudentPaymentStatus.PENDING 
 
    def test_duplicate_reference_raises_error(self): 
        """Cannot submit reference for a month already submitted.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        use_case = SubmitPaymentReferenceUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        use_case.execute(SubmitPaymentReferenceCommand( 
            student_id=student_id, 
            payment_month="2025-06", 
            reference_number="TXN-001", 
            due_date=date(2025, 6, 30), 
            amount=500.0, 
            currency="ETB", 
        )) 
 
        with pytest.raises(DuplicatePaymentError): 
            use_case.execute(SubmitPaymentReferenceCommand( 
                student_id=student_id, 
                payment_month="2025-06", 
                reference_number="TXN-002", 
                due_date=date(2025, 6, 30), 
                amount=500.0, 
                currency="ETB", 
            )) 
 
    def test_publishes_payment_recorded_event(self): 
        """Payment recorded event published on reference submission.""" 
        repo = FakeStudentPaymentRepository() 
        event_publisher = FakeEventPublisher() 
        use_case = SubmitPaymentReferenceUseCase( 
            student_payment_repository=repo, 
            event_publisher=event_publisher, 
        ) 
 
        use_case.execute(SubmitPaymentReferenceCommand( 
            student_id=uuid4(), 
            payment_month="2025-06", 
            reference_number="TXN-001", 
            due_date=date(2025, 6, 30), 
            amount=500.0, 
            currency="ETB", 
        )) 
 
        events = event_publisher.get_events_of_type( 
            "student_payment_recorded" 
        ) 
        assert len(events) == 1 
 
 
# ── GetStudentPaymentHistory Tests 
 
class TestGetStudentPaymentHistory: 
 
    def test_returns_all_payments_for_student(self): 
        """Returns all payment records for a student.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        make_payment(repo, student_id=student_id, payment_month="2025-05") 
        make_payment(repo, student_id=student_id, payment_month="2025-06") 
        make_payment(repo, payment_month="2025-06")  # other student 
        use_case = GetStudentPaymentHistoryUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute( 
            GetStudentPaymentHistoryCommand(student_id=student_id) 
        ) 
 
        assert len(result.payments) == 2 
        assert result.student_id == student_id 
 
    def test_returns_empty_for_student_with_no_payments(self): 
        """Returns empty list for student with no payment history.""" 
        repo = FakeStudentPaymentRepository() 
        use_case = GetStudentPaymentHistoryUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute( 
            GetStudentPaymentHistoryCommand(student_id=uuid4()) 
        ) 
 
        assert result.payments == [] 
 
 
# ── GetSubscriptionStatus Tests 
 
class TestGetSubscriptionStatus: 
 
    def test_returns_paid_status_when_current_month_paid(self): 
        """Returns PAID when current month payment is verified.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        make_payment( 
            repo, 
            student_id=student_id, 
            payment_month="2025-06", 
            status=StudentPaymentStatus.PAID, 
        ) 
        use_case = GetSubscriptionStatusUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute(GetSubscriptionStatusCommand( 
            student_id=student_id, 
            current_month="2025-06", 
        )) 
 
        assert result.current_month_paid is True 
        assert result.subscription_status == StudentPaymentStatus.PAID 
 
    def test_returns_pending_when_no_payments(self): 
        """Returns PENDING status for student with no payments.""" 
        repo = FakeStudentPaymentRepository() 
        use_case = GetSubscriptionStatusUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute(GetSubscriptionStatusCommand( 
            student_id=uuid4(), 
            current_month="2025-06", 
        )) 
 
        assert result.current_month_paid is False 
        assert result.subscription_status == StudentPaymentStatus.PENDING 
 
    def test_current_month_not_paid_when_pending(self): 
        """current_month_paid is False when payment is still PENDING.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        make_payment( 
            repo, 
            student_id=student_id, 
            payment_month="2025-06", 
            status=StudentPaymentStatus.PENDING, 
        ) 
        use_case = GetSubscriptionStatusUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute(GetSubscriptionStatusCommand( 
            student_id=student_id, 
            current_month="2025-06", 
        )) 
 
        assert result.current_month_paid is False 
 
 
# ── UpdateStudentPaymentStatus Tests 
 
class TestUpdateStudentPaymentStatus: 
 
    def test_pending_to_paid_succeeds(self): 
        """PENDING → PAID is a valid transition.""" 
        repo = FakeStudentPaymentRepository() 
        event_publisher = FakeEventPublisher() 
        student_id = uuid4() 
        payment = make_payment( 
            repo, 
            student_id=student_id, 
            status=StudentPaymentStatus.PENDING, 
        ) 
        admin_id = uuid4() 
        use_case = UpdateStudentPaymentStatusUseCase( 
            student_payment_repository=repo, 
            event_publisher=event_publisher, 
        ) 
 
        result = use_case.execute(UpdateStudentPaymentStatusCommand( 
            student_id=student_id, 
            payment_id=payment.id, 
            new_status=StudentPaymentStatus.PAID, 
            verified_by=admin_id, 
        )) 
 
        assert result.status == StudentPaymentStatus.PAID 
        assert result.verified_by == admin_id 
        assert result.verified_at is not None 
 
    def test_pending_to_failed_succeeds(self): 
        """PENDING → FAILED is valid when admin rejects reference.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        payment = make_payment( 
            repo, student_id=student_id, 
            status=StudentPaymentStatus.PENDING, 
        ) 
        use_case = UpdateStudentPaymentStatusUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(UpdateStudentPaymentStatusCommand( 
            student_id=student_id, 
            payment_id=payment.id, 
            new_status=StudentPaymentStatus.FAILED, 
            note="Reference number not found", 
        )) 
 
        assert result.status == StudentPaymentStatus.FAILED 
        assert result.note == "Reference number not found" 
 
    def test_pending_to_overdue_succeeds(self): 
        """PENDING → OVERDUE is valid when deadline passes.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        payment = make_payment( 
            repo, student_id=student_id, 
            status=StudentPaymentStatus.PENDING, 
        ) 
        use_case = UpdateStudentPaymentStatusUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(UpdateStudentPaymentStatusCommand( 
            student_id=student_id, 
            payment_id=payment.id, 
            new_status=StudentPaymentStatus.OVERDUE, 
        )) 
 
        assert result.status == StudentPaymentStatus.OVERDUE 
 
    def test_paid_to_pending_is_invalid(self): 
        """PAID → PENDING is not a valid transition.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        payment = make_payment( 
            repo, student_id=student_id, 
            status=StudentPaymentStatus.PAID, 
        ) 
        use_case = UpdateStudentPaymentStatusUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        with pytest.raises(InvalidPaymentStatusTransitionError): 
            use_case.execute(UpdateStudentPaymentStatusCommand( 
                student_id=student_id, 
                payment_id=payment.id, 
                new_status=StudentPaymentStatus.PENDING, 
            )) 
 
    def test_failed_to_paid_is_invalid(self): 
        """FAILED → PAID is not valid — once failed, record is final.""" 
        repo = FakeStudentPaymentRepository() 
        student_id = uuid4() 
        payment = make_payment( 
            repo, student_id=student_id, 
            status=StudentPaymentStatus.FAILED, 
        ) 
        use_case = UpdateStudentPaymentStatusUseCase( 
            student_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        with pytest.raises(InvalidPaymentStatusTransitionError): 
            use_case.execute(UpdateStudentPaymentStatusCommand( 
                student_id=student_id, 
                payment_id=payment.id, 
                new_status=StudentPaymentStatus.PAID, 
            )) 
 
    def test_publishes_status_changed_event(self): 
        """StudentPaymentStatusChanged event published on update.""" 
        repo = FakeStudentPaymentRepository() 
        event_publisher = FakeEventPublisher() 
        student_id = uuid4() 
        payment = make_payment( 
            repo, student_id=student_id, 
            status=StudentPaymentStatus.PENDING, 
        ) 
        use_case = UpdateStudentPaymentStatusUseCase( 
            student_payment_repository=repo, 
            event_publisher=event_publisher, 
        ) 
 
        use_case.execute(UpdateStudentPaymentStatusCommand( 
            student_id=student_id, 
            payment_id=payment.id, 
            new_status=StudentPaymentStatus.PAID, 
            verified_by=uuid4(), 
        )) 
 
        events = event_publisher.get_events_of_type( 
            "student_payment_status_changed" 
        ) 
        assert len(events) == 1 
 
    def test_nonexistent_payment_raises_error(self): 
        """Updating nonexistent payment raises error.""" 
        use_case = UpdateStudentPaymentStatusUseCase( 
            student_payment_repository=FakeStudentPaymentRepository(), 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        with pytest.raises(StudentPaymentNotFoundError): 
            use_case.execute(UpdateStudentPaymentStatusCommand( 
                student_id=uuid4(), 
                payment_id=uuid4(), 
                new_status=StudentPaymentStatus.PAID, 
            )) 
 
 
# ── ListOverdueStudents Tests 
 
 
class TestListOverdueStudents: 
 
    def test_returns_overdue_payments(self): 
        """Returns all payments with OVERDUE status.""" 
        repo = FakeStudentPaymentRepository() 
        make_payment(repo, status=StudentPaymentStatus.OVERDUE) 
        make_payment(repo, status=StudentPaymentStatus.OVERDUE) 
        make_payment(repo, status=StudentPaymentStatus.PAID) 
        use_case = ListOverdueStudentsUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute(ListOverdueStudentsCommand()) 
 
        assert result.overdue_count == 2 
        assert len(result.payments) == 2 
 
    def test_returns_empty_when_no_overdue(self): 
        """Returns empty when no overdue payments.""" 
        repo = FakeStudentPaymentRepository() 
        make_payment(repo, status=StudentPaymentStatus.PAID) 
        use_case = ListOverdueStudentsUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute(ListOverdueStudentsCommand()) 
 
        assert result.overdue_count == 0 
        assert result.payments == [] 
 
 
# ── ListPendingVerification Tests 
 
 
class TestListPendingVerification: 
 
    def test_returns_pending_payments(self): 
        """Returns all payments awaiting admin verification.""" 
        repo = FakeStudentPaymentRepository() 
        make_payment(repo, status=StudentPaymentStatus.PENDING) 
        make_payment(repo, status=StudentPaymentStatus.PENDING) 
        make_payment(repo, status=StudentPaymentStatus.PAID) 
        use_case = ListPendingVerificationUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute(ListPendingVerificationCommand()) 
 
        assert len(result) == 2 
        assert all( 
            p.status == StudentPaymentStatus.PENDING for p in result 
        ) 
 
    def test_returns_empty_when_no_pending(self): 
        """Returns empty when no payments pending verification.""" 
        repo = FakeStudentPaymentRepository() 
        make_payment(repo, status=StudentPaymentStatus.PAID) 
        use_case = ListPendingVerificationUseCase( 
            student_payment_repository=repo, 
        ) 
 
        result = use_case.execute(ListPendingVerificationCommand()) 
 
        assert result == [] 