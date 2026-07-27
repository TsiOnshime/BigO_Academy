from dataclasses import dataclass 
from uuid import UUID 
from typing import Optional 
 
from domain.models import StudentPayment 
from domain.enums import StudentPaymentStatus 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
 
 
@dataclass 
class GetStudentPaymentReportCommand: 
    cohort_id: Optional[UUID] = None 
    status: Optional[StudentPaymentStatus] = None 
    month: Optional[str] = None 
    page: int = 0 
    size: int = 20 
 
 
@dataclass 
class GetStudentPaymentReportResult: 
    payments: list[StudentPayment] 
    month: Optional[str] 
    cohort_id: Optional[UUID] 
 
 
class GetStudentPaymentReportUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
 
    def execute( 
        self, command: GetStudentPaymentReportCommand 
    ) -> GetStudentPaymentReportResult: 
 
        if command.status is not None: 
            payments = self.student_payment_repository.find_by_status( 
                status=command.status, 
                cohort_id=command.cohort_id, 
                page=command.page, 
                size=command.size, 
            ) 
        else: 
            # No status filter — return all for cohort or all 
            payments = self.student_payment_repository.find_by_status( 
                status=StudentPaymentStatus.PENDING, 
                cohort_id=command.cohort_id, 
            ) + self.student_payment_repository.find_by_status( 
                status=StudentPaymentStatus.PAID, 
                cohort_id=command.cohort_id, 
            ) + self.student_payment_repository.find_by_status( 
                status=StudentPaymentStatus.OVERDUE, 
                cohort_id=command.cohort_id, 
            ) + self.student_payment_repository.find_by_status( 
                status=StudentPaymentStatus.FAILED, 
                cohort_id=command.cohort_id, 
            ) 
 
        return GetStudentPaymentReportResult( 
            payments=payments, 
            month=command.month, 
            cohort_id=command.cohort_id, 
        )