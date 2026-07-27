from dataclasses import dataclass 
from uuid import UUID 
from typing import Optional 
 
from domain.models import StudentPayment 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
from domain.enums import StudentPaymentStatus 
 
 
@dataclass 
class ListOverdueStudentsCommand: 
    cohort_id: Optional[UUID] = None 
    page: int = 0 
    size: int = 20 
 
 
@dataclass 
class ListOverdueStudentsResult: 
    payments: list[StudentPayment] 
    overdue_count: int 
 
 
class ListOverdueStudentsUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
 
    def execute( 
        self, command: ListOverdueStudentsCommand 
    ) -> ListOverdueStudentsResult: 
 
        payments = self.student_payment_repository.find_by_status( 
            status=StudentPaymentStatus.OVERDUE, 
            cohort_id=command.cohort_id, 
            page=command.page, 
            size=command.size, 
        ) 
 
        return ListOverdueStudentsResult( 
            payments=payments, 
            overdue_count=len(payments), 
        )