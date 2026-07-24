from dataclasses import dataclass 
from uuid import UUID 
from datetime import datetime, timezone 
from typing import Optional 
 
from domain.models import StudentPayment 
from domain.enums import StudentPaymentStatus 
from domain.exceptions import ( 
    StudentPaymentNotFoundError, 
    InvalidPaymentStatusTransitionError, 
) 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
from application.ports.outbound.event_publisher import EventPublisherPort 
 
 
@dataclass 
class UpdateStudentPaymentStatusCommand: 
    student_id: UUID 
    payment_id: UUID 
    new_status: StudentPaymentStatus 
    verified_by: Optional[UUID] = None   # required when PAID 
    note: Optional[str] = None 
 
 
class UpdateStudentPaymentStatusUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
        event_publisher: EventPublisherPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
        self.event_publisher = event_publisher 
 
    def execute( 
        self, command: UpdateStudentPaymentStatusCommand 
    ) -> StudentPayment: 
 
        payment = self.student_payment_repository.find_by_id( 
            command.payment_id 
        ) 
        if payment is None: 
            raise StudentPaymentNotFoundError(str(command.payment_id)) 
 
        # Enforce valid transitions using domain model 
        if not payment.can_transition_to(command.new_status): 
            raise InvalidPaymentStatusTransitionError( 
                current_status=payment.status.value, 
                target_status=command.new_status.value, 
            ) 
 
        old_status = payment.status 
        payment.status = command.new_status 
        payment.note = command.note 
 
        # Set verification fields when marking as PAID 
        if command.new_status == StudentPaymentStatus.PAID: 
            payment.verified_by = command.verified_by 
            payment.verified_at = datetime.now(timezone.utc) 
 
        saved_payment = self.student_payment_repository.save(payment) 
 
        self.event_publisher.publish_student_payment_status_changed( 
            saved_payment, 
            old_status.value, 
        ) 
 
        return saved_payment 