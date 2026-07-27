from dataclasses import dataclass 
from typing import Optional 
 
from domain.enums import StudentPaymentStatus, TeacherPaymentStatus 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort 
 
 
@dataclass 
class GetPaymentSummaryCommand: 
    month: Optional[str] = None     # "YYYY-MM" — defaults to current month 
 
 
@dataclass 
class StudentPaymentSummary: 
    total_paid: int 
    total_pending: int 
    total_overdue: int 
    total_amount_collected: float 
    currency: str 
 
 
@dataclass 
class TeacherPaymentSummary: 
    total_paid: int 
    total_pending: int 
    total_amount_paid: float 
    total_amount_pending: float 
    currency: str 
 
 
@dataclass 
class GetPaymentSummaryResult: 
    month: str 
    student_payments: StudentPaymentSummary 
    teacher_payments: TeacherPaymentSummary 
 
 
class GetPaymentSummaryUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
        teacher_payment_repository: TeacherPaymentRepositoryPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
        self.teacher_payment_repository = teacher_payment_repository 
 
    def execute( 
        self, command: GetPaymentSummaryCommand 
    ) -> GetPaymentSummaryResult: 
 
        from datetime import datetime 
        month = command.month or datetime.now().strftime("%Y-%m") 
 
        # Student payment summary 
        paid_students = self.student_payment_repository.find_by_status( 
            StudentPaymentStatus.PAID 
        ) 
        pending_students = self.student_payment_repository.find_by_status( 
            StudentPaymentStatus.PENDING 
        ) 
        overdue_students = self.student_payment_repository.find_by_status( 
            StudentPaymentStatus.OVERDUE 
        ) 
 
        student_summary = StudentPaymentSummary( 
            total_paid=len(paid_students), 
            total_pending=len(pending_students), 
            total_overdue=len(overdue_students), 
            total_amount_collected=sum(p.amount for p in paid_students), 
            currency="ETB", 
        ) 
 
        # Teacher payment summary 
        paid_teachers = self.teacher_payment_repository.find_by_status( 
            TeacherPaymentStatus.PAID 
        ) 
        pending_teachers = self.teacher_payment_repository.find_by_status( 
            TeacherPaymentStatus.PENDING 
        ) 
 
        teacher_summary = TeacherPaymentSummary( 
            total_paid=len(paid_teachers), 
            total_pending=len(pending_teachers), 
            total_amount_paid=sum(p.amount for p in paid_teachers), 
            total_amount_pending=sum(p.amount for p in pending_teachers), 
            currency="ETB", 
        ) 
 
        return GetPaymentSummaryResult( 
            month=month, 
            student_payments=student_summary, 
            teacher_payments=teacher_summary, 
        ) 