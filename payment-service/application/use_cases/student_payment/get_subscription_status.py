from dataclasses import dataclass 
from uuid import UUID 
from typing import Optional 
from datetime import date 
 
from domain.enums import StudentPaymentStatus 
from domain.models import StudentPayment 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
 
 
@dataclass 
class GetSubscriptionStatusCommand: 
    student_id: UUID 
    current_month: str      # "YYYY-MM" — caller passes current month 
 
 
@dataclass 
class GetSubscriptionStatusResult: 
    student_id: UUID 
    subscription_status: StudentPaymentStatus 
    current_month_paid: bool 
    next_due_date: Optional[date] 
    last_payment_date: Optional[date] 
    last_payment_amount: Optional[float] 
 
 
class GetSubscriptionStatusUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
 
    def execute( 
        self, command: GetSubscriptionStatusCommand 
    ) -> GetSubscriptionStatusResult: 
 
        # Check current month payment 
        current_payment = ( 
            self.student_payment_repository.find_by_student_and_month( 
                command.student_id, 
                command.current_month, 
            ) 
        ) 
 
        # Get full history to find last payment 
        all_payments = self.student_payment_repository.find_by_student( 
            student_id=command.student_id, 
        ) 
 
        paid_payments = [p for p in all_payments if p.is_paid()] 
        last_payment = paid_payments[0] if paid_payments else None 
 
        # Determine overall subscription status 
        if current_payment is not None: 
            subscription_status = current_payment.status 
        elif last_payment is not None: 
            subscription_status = StudentPaymentStatus.OVERDUE 
        else: 
            subscription_status = StudentPaymentStatus.PENDING 
 
        return GetSubscriptionStatusResult( 
            student_id=command.student_id, 
            subscription_status=subscription_status, 
            current_month_paid=( 
                current_payment is not None and current_payment.is_paid() 
            ), 
            next_due_date=( 
                current_payment.due_date if current_payment else None 
            ), 
            last_payment_date=( 
                last_payment.verified_at.date() 
                if last_payment and last_payment.verified_at 
                else None 
            ), 
            last_payment_amount=( 
                last_payment.amount if last_payment else None 
            ), 
        ) 