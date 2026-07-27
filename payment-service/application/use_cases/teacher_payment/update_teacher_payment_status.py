from dataclasses import dataclass 
from uuid import UUID 
from datetime import datetime, timezone 
from typing import Optional 
 
from domain.models import TeacherPayment 
from domain.enums import TeacherPaymentStatus 
from domain.exceptions import ( 
    TeacherPaymentNotFoundError, 
    InvalidPaymentStatusTransitionError, 
) 
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort 
from application.ports.outbound.event_publisher import EventPublisherPort 
 
 
@dataclass 
class UpdateTeacherPaymentStatusCommand: 
    teacher_id: UUID 
    payment_id: UUID 
    new_status: TeacherPaymentStatus 
    processed_by: Optional[UUID] = None 
    note: Optional[str] = None 
 
 
class UpdateTeacherPaymentStatusUseCase: 
 
    def __init__( 
        self, 
        teacher_payment_repository: TeacherPaymentRepositoryPort, 
        event_publisher: EventPublisherPort, 
    ): 
        self.teacher_payment_repository = teacher_payment_repository 
        self.event_publisher = event_publisher 
 
    def execute( 
        self, command: UpdateTeacherPaymentStatusCommand 
    ) -> TeacherPayment: 
 
        payment = self.teacher_payment_repository.find_by_id( 
            command.payment_id 
        ) 
        if payment is None: 
            raise TeacherPaymentNotFoundError(str(command.payment_id)) 
 
        if not payment.can_transition_to(command.new_status): 
            raise InvalidPaymentStatusTransitionError( 
                current_status=payment.status.value, 
                target_status=command.new_status.value, 
            ) 
 
        old_status = payment.status 
        payment.status = command.new_status 
        payment.note = command.note 
 
        if command.new_status == TeacherPaymentStatus.PAID: 
            payment.processed_by = command.processed_by 
            payment.processed_at = datetime.now(timezone.utc) 
 
        saved_payment = self.teacher_payment_repository.save(payment) 
 
        self.event_publisher.publish_teacher_payment_status_changed( 
            saved_payment, 
            old_status.value, 
        ) 
 
        return saved_payment