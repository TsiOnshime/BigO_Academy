from dataclasses import dataclass 
from uuid import uuid4, UUID 
from typing import Optional 
 
from domain.models import TeacherPayment 
from domain.enums import TeacherPaymentStatus 
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort 
from application.ports.outbound.event_publisher import EventPublisherPort 
 
 
@dataclass 
class RecordTeacherPaymentCommand: 
    teacher_id: UUID 
    payment_month: str 
    amount: float 
    currency: str 
    note: Optional[str] = None 
 
 
@dataclass 
class RecordTeacherPaymentResult: 
    payment: TeacherPayment 
 
 
class RecordTeacherPaymentUseCase: 
 
    def __init__( 
        self, 
        teacher_payment_repository: TeacherPaymentRepositoryPort, 
        event_publisher: EventPublisherPort, 
    ): 
        self.teacher_payment_repository = teacher_payment_repository 
        self.event_publisher = event_publisher 
 
    def execute( 
        self, command: RecordTeacherPaymentCommand 
    ) -> RecordTeacherPaymentResult: 
 
        new_payment = TeacherPayment( 
            id=uuid4(), 
            teacher_id=command.teacher_id, 
            payment_month=command.payment_month, 
            amount=command.amount, 
            currency=command.currency, 
            status=TeacherPaymentStatus.PENDING, 
            note=command.note, 
            processed_by=None, 
            processed_at=None, 
        ) 
 
        saved_payment = self.teacher_payment_repository.save(new_payment) 
        self.event_publisher.publish_teacher_payment_recorded(saved_payment) 
 
        return RecordTeacherPaymentResult(payment=saved_payment)