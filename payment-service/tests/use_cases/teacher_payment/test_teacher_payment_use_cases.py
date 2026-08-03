import pytest 
from uuid import uuid4 
 
from domain.enums import TeacherPaymentStatus 
from domain.exceptions import ( 
    TeacherPaymentNotFoundError, 
    InvalidPaymentStatusTransitionError, 
) 
from domain.models import TeacherPayment 
from application.use_cases.teacher_payment.record_teacher_payment import ( 
    RecordTeacherPaymentUseCase, RecordTeacherPaymentCommand, 
) 
from application.use_cases.teacher_payment.get_teacher_payment_history import ( 
    GetTeacherPaymentHistoryUseCase, GetTeacherPaymentHistoryCommand, 
) 
from application.use_cases.teacher_payment.update_teacher_payment_status import ( 
    UpdateTeacherPaymentStatusUseCase, UpdateTeacherPaymentStatusCommand, 
) 
from application.use_cases.teacher_payment.list_pending_teacher_payments import ( 
    ListPendingTeacherPaymentsUseCase, ListPendingTeacherPaymentsCommand, 
) 
from tests.fakes import FakeTeacherPaymentRepository, FakeEventPublisher 
 
 
# ── Helpers 
 
def make_payment( 
    repo: FakeTeacherPaymentRepository, 
    teacher_id=None, 
    **overrides, 
) -> TeacherPayment: 
    defaults = { 
        "id": uuid4(), 
        "teacher_id": teacher_id or uuid4(), 
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
 
 
# ── RecordTeacherPayment Tests 
 
 
class TestRecordTeacherPayment: 
 
    def test_records_payment_successfully(self): 
        """Admin records a teacher payment successfully.""" 
        repo = FakeTeacherPaymentRepository() 
        use_case = RecordTeacherPaymentUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(RecordTeacherPaymentCommand( 
            teacher_id=uuid4(), 
            payment_month="2025-06", 
            amount=3000.0, 
            currency="ETB", 
        )) 
 
        assert result.payment.amount == 3000.0 
        assert result.payment.payment_month == "2025-06" 
 
    def test_new_payment_starts_pending(self): 
        """New teacher payment starts as PENDING.""" 
        repo = FakeTeacherPaymentRepository() 
        use_case = RecordTeacherPaymentUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(RecordTeacherPaymentCommand( 
            teacher_id=uuid4(), 
            payment_month="2025-06", 
            amount=3000.0, 
            currency="ETB", 
        )) 
 
        assert result.payment.status == TeacherPaymentStatus.PENDING.value
 
    def test_publishes_payment_recorded_event(self): 
        """TeacherPaymentRecorded event published.""" 
        repo = FakeTeacherPaymentRepository() 
        event_publisher = FakeEventPublisher() 
        use_case = RecordTeacherPaymentUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=event_publisher, 
        ) 
 
        use_case.execute(RecordTeacherPaymentCommand( 
            teacher_id=uuid4(), 
            payment_month="2025-06", 
            amount=3000.0, 
            currency="ETB", 
        )) 
 
        events = event_publisher.get_events_of_type( 
            "teacher_payment_recorded" 
        ) 
        assert len(events) == 1 
 
 
# ── GetTeacherPaymentHistory Tests 
 
 
class TestGetTeacherPaymentHistory: 
 
    def test_returns_all_payments_for_teacher(self): 
        """Returns all payment records for a teacher.""" 
        repo = FakeTeacherPaymentRepository() 
        teacher_id = uuid4() 
        make_payment(repo, teacher_id=teacher_id, payment_month="2025-05") 
        make_payment(repo, teacher_id=teacher_id, payment_month="2025-06") 
        make_payment(repo, payment_month="2025-06")  # other teacher 
        use_case = GetTeacherPaymentHistoryUseCase( 
            teacher_payment_repository=repo, 
        ) 
 
        result = use_case.execute( 
            GetTeacherPaymentHistoryCommand(teacher_id=teacher_id) 
        ) 
 
        assert len(result.payments) == 2 
        assert result.teacher_id == teacher_id 
 
    def test_returns_empty_for_teacher_with_no_payments(self): 
        """Returns empty list for teacher with no payments.""" 
        repo = FakeTeacherPaymentRepository() 
        use_case = GetTeacherPaymentHistoryUseCase( 
            teacher_payment_repository=repo, 
        ) 
 
        result = use_case.execute( 
            GetTeacherPaymentHistoryCommand(teacher_id=uuid4()) 
        ) 
 
        assert result.payments == [] 
 
 
# ── UpdateTeacherPaymentStatus Tests 
 
class TestUpdateTeacherPaymentStatus: 
 
    def test_pending_to_paid_succeeds(self): 
        """PENDING → PAID is valid.""" 
        repo = FakeTeacherPaymentRepository() 
        event_publisher = FakeEventPublisher() 
        teacher_id = uuid4() 
        payment = make_payment( 
            repo, teacher_id=teacher_id, 
            status=TeacherPaymentStatus.PENDING, 
        ) 
        admin_id = uuid4() 
        use_case = UpdateTeacherPaymentStatusUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=event_publisher, 
        ) 
 
        result = use_case.execute(UpdateTeacherPaymentStatusCommand( 
            teacher_id=teacher_id, 
            payment_id=payment.id, 
            new_status=TeacherPaymentStatus.PAID, 
            processed_by=admin_id, 
        )) 
 
        assert result.status == TeacherPaymentStatus.PAID 
        assert result.processed_by == admin_id 
        assert result.processed_at is not None 
 
    def test_pending_to_cancelled_succeeds(self): 
        """PENDING → CANCELLED is valid.""" 
        repo = FakeTeacherPaymentRepository() 
        teacher_id = uuid4() 
        payment = make_payment( 
            repo, teacher_id=teacher_id, 
            status=TeacherPaymentStatus.PENDING, 
        ) 
        use_case = UpdateTeacherPaymentStatusUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        result = use_case.execute(UpdateTeacherPaymentStatusCommand( 
            teacher_id=teacher_id, 
            payment_id=payment.id, 
            new_status=TeacherPaymentStatus.CANCELLED, 
        )) 
 
        assert result.status == TeacherPaymentStatus.CANCELLED 
 
    def test_paid_to_pending_is_invalid(self): 
        """PAID → PENDING is not valid.""" 
        repo = FakeTeacherPaymentRepository() 
        teacher_id = uuid4() 
        payment = make_payment( 
            repo, teacher_id=teacher_id, 
            status=TeacherPaymentStatus.PAID, 
        ) 
        use_case = UpdateTeacherPaymentStatusUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        with pytest.raises(InvalidPaymentStatusTransitionError): 
            use_case.execute(UpdateTeacherPaymentStatusCommand( 
                teacher_id=teacher_id, 
                payment_id=payment.id, 
                new_status=TeacherPaymentStatus.PENDING, 
            )) 
 
    def test_cancelled_to_paid_is_invalid(self): 
        """CANCELLED → PAID is not valid.""" 
        repo = FakeTeacherPaymentRepository() 
        teacher_id = uuid4() 
        payment = make_payment( 
            repo, teacher_id=teacher_id, 
            status=TeacherPaymentStatus.CANCELLED, 
        ) 
        use_case = UpdateTeacherPaymentStatusUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        with pytest.raises(InvalidPaymentStatusTransitionError): 
            use_case.execute(UpdateTeacherPaymentStatusCommand( 
                teacher_id=teacher_id, 
                payment_id=payment.id, 
                new_status=TeacherPaymentStatus.PAID, 
            )) 
 
    def test_publishes_status_changed_event(self): 
        """TeacherPaymentStatusChanged event published on update.""" 
        repo = FakeTeacherPaymentRepository() 
        event_publisher = FakeEventPublisher() 
        teacher_id = uuid4() 
        payment = make_payment( 
            repo, teacher_id=teacher_id, 
            status=TeacherPaymentStatus.PENDING, 
        ) 
        use_case = UpdateTeacherPaymentStatusUseCase( 
            teacher_payment_repository=repo, 
            event_publisher=event_publisher, 
        ) 
 
        use_case.execute(UpdateTeacherPaymentStatusCommand( 
            teacher_id=teacher_id, 
            payment_id=payment.id, 
            new_status=TeacherPaymentStatus.PAID, 
            processed_by=uuid4(), 
        )) 
 
        events = event_publisher.get_events_of_type( 
            "teacher_payment_status_changed" 
        ) 
        assert len(events) == 1 
 
    def test_nonexistent_payment_raises_error(self): 
        """Updating nonexistent payment raises error.""" 
        use_case = UpdateTeacherPaymentStatusUseCase( 
            teacher_payment_repository=FakeTeacherPaymentRepository(), 
            event_publisher=FakeEventPublisher(), 
        ) 
 
        with pytest.raises(TeacherPaymentNotFoundError): 
            use_case.execute(UpdateTeacherPaymentStatusCommand( 
                teacher_id=uuid4(), 
                payment_id=uuid4(), 
                new_status=TeacherPaymentStatus.PAID, 
            )) 
 
 
# ── ListPendingTeacherPayments Tests 
 
 
class TestListPendingTeacherPayments: 
 
    def test_returns_pending_payments(self): 
        """Returns all teacher payments awaiting processing.""" 
        repo = FakeTeacherPaymentRepository() 
        make_payment(repo, status=TeacherPaymentStatus.PENDING) 
        make_payment(repo, status=TeacherPaymentStatus.PENDING) 
        make_payment(repo, status=TeacherPaymentStatus.PAID) 
        use_case = ListPendingTeacherPaymentsUseCase( 
            teacher_payment_repository=repo, 
        ) 
 
        result = use_case.execute(ListPendingTeacherPaymentsCommand()) 
 
        assert len(result) == 2 
        assert all( 
            p.status == TeacherPaymentStatus.PENDING for p in result 
        ) 
 
    def test_returns_empty_when_no_pending(self): 
        """Returns empty when all payments are processed.""" 
        repo = FakeTeacherPaymentRepository() 
        make_payment(repo, status=TeacherPaymentStatus.PAID) 
        use_case = ListPendingTeacherPaymentsUseCase( 
            teacher_payment_repository=repo, 
        ) 
 
        result = use_case.execute(ListPendingTeacherPaymentsCommand()) 
 
        assert result == [] 