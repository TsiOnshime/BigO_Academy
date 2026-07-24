from uuid import UUID 
from typing import Optional 
from datetime import date 
 
from domain.models import StudentPayment, TeacherPayment 
from domain.enums import StudentPaymentStatus, TeacherPaymentStatus 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort 
from application.ports.outbound.event_publisher import EventPublisherPort 
 
 
class FakeStudentPaymentRepository(StudentPaymentRepositoryPort): 
 
    def __init__(self): 
        self._store: dict[UUID, StudentPayment] = {} 
 
    def save(self, payment: StudentPayment) -> StudentPayment: 
        self._store[payment.id] = payment 
        return payment 
 
    def find_by_id(self, payment_id: UUID) -> Optional[StudentPayment]: 
        return self._store.get(payment_id) 
 
    def find_by_student( 
        self, student_id: UUID, page: int = 0, size: int = 20 
    ) -> list[StudentPayment]: 
        results = [ 
            p for p in self._store.values() 
            if p.student_id == student_id 
        ] 
        return sorted( 
            results, 
            key=lambda p: p.created_at, 
            reverse=True, 
        ) 
 
    def find_by_student_and_month( 
        self, student_id: UUID, payment_month: str 
    ) -> Optional[StudentPayment]: 
        for p in self._store.values(): 
            if p.student_id == student_id and p.payment_month == payment_month: 
                return p 
        return None 
 
    def find_by_status( 
        self, 
        status: StudentPaymentStatus, 
        cohort_id: Optional[UUID] = None, 
        page: int = 0, 
        size: int = 20, 
    ) -> list[StudentPayment]: 
        return [ 
            p for p in self._store.values() 
            if p.status == status 
        ] 
 
    def find_overdue(self) -> list[StudentPayment]: 
        from datetime import date 
        today = date.today() 
        return [ 
            p for p in self._store.values() 
            if p.status == StudentPaymentStatus.PENDING 
            and p.due_date < today 
        ] 
 
 
class FakeTeacherPaymentRepository(TeacherPaymentRepositoryPort): 
 
    def __init__(self): 
        self._store: dict[UUID, TeacherPayment] = {} 
 
    def save(self, payment: TeacherPayment) -> TeacherPayment: 
        self._store[payment.id] = payment 
        return payment 
 
    def find_by_id(self, payment_id: UUID) -> Optional[TeacherPayment]: 
        return self._store.get(payment_id) 
 
    def find_by_teacher( 
        self, teacher_id: UUID, page: int = 0, size: int = 20 
    ) -> list[TeacherPayment]: 
        return [ 
            p for p in self._store.values() 
            if p.teacher_id == teacher_id 
        ] 
 
    def find_by_status( 
        self, 
        status: TeacherPaymentStatus, 
        page: int = 0, 
        size: int = 20, 
    ) -> list[TeacherPayment]: 
        return [ 
            p for p in self._store.values() 
            if p.status == status 
        ] 
 
    def find_by_month(self, payment_month: str) -> list[TeacherPayment]: 
        return [ 
            p for p in self._store.values() 
            if p.payment_month == payment_month 
        ] 
 
 
class FakeEventPublisher(EventPublisherPort): 
 
    def __init__(self): 
        self.published_events: list[dict] = [] 
 
    def _record(self, event_type: str, **kwargs): 
        self.published_events.append({"type": event_type, **kwargs}) 
 
    def get_events_of_type(self, event_type: str) -> list[dict]: 
        return [e for e in self.published_events if e["type"] == event_type] 
 
    def publish_student_payment_recorded(self, payment): 
        self._record( 
            "student_payment_recorded", 
            payment_id=payment.id, 
            student_id=payment.student_id, 
        ) 
 
    def publish_student_payment_status_changed(self, payment, old_status): 
        self._record( 
            "student_payment_status_changed", 
            payment_id=payment.id, 
            old_status=old_status, 
            new_status=payment.status.value, 
        ) 
 
    def publish_teacher_payment_recorded(self, payment): 
        self._record( 
            "teacher_payment_recorded", 
            payment_id=payment.id, 
            teacher_id=payment.teacher_id, 
        ) 
 
    def publish_teacher_payment_status_changed(self, payment, old_status): 
        self._record( 
            "teacher_payment_status_changed", 
            payment_id=payment.id, 
            old_status=old_status, 
            new_status=payment.status.value, 
        ) 