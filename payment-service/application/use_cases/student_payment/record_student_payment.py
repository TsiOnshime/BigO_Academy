from dataclasses import dataclass 
from datetime import date 
from uuid import uuid4, UUID 
from typing import Optional 
from domain.models import StudentPayment 
from domain.enums import StudentPaymentStatus 
from domain.exceptions import DuplicatePaymentError 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
from application.ports.outbound.event_publisher import EventPublisherPort 
 
 
@dataclass 
class RecordStudentPaymentCommand: 
    student_id: UUID 
    payment_month: str          # "YYYY-MM" 
    amount: float 
    currency: str 
    due_date: date 
    reference_number: Optional[str] = None 
    note: Optional[str] = None 
 
 
@dataclass 
class RecordStudentPaymentResult: 
    payment: StudentPayment 
 
 
class RecordStudentPaymentUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
        event_publisher: EventPublisherPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
        self.event_publisher = event_publisher 
 
    def execute( 
        self, command: RecordStudentPaymentCommand 
    ) -> RecordStudentPaymentResult: 
 
        # Check for duplicate payment for same student and month 
        existing = self.student_payment_repository.find_by_student_and_month( 
            command.student_id, 
            command.payment_month, 
        ) 
        if existing is not None: 
            raise DuplicatePaymentError( 
                str(command.student_id), 
                command.payment_month, 
            ) 
 
        # Admin records payment — starts as PENDING awaiting verification 
        new_payment = StudentPayment( 
            id=uuid4(), 
            student_id=command.student_id, 
            payment_month=command.payment_month, 
            amount=command.amount, 
            currency=command.currency, 
            status=StudentPaymentStatus.PENDING, 
            reference_number=command.reference_number, 
            note=command.note, 
            verified_by=None, 
            verified_at=None, 
            due_date=command.due_date, 
        ) 
 
        saved_payment = self.student_payment_repository.save(new_payment) 
        self.event_publisher.publish_student_payment_recorded(saved_payment) 
 
        return RecordStudentPaymentResult(payment=saved_payment)