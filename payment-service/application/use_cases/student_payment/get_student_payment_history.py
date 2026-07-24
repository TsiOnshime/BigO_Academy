from dataclasses import dataclass 
from uuid import UUID 
 
from domain.models import StudentPayment 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
 
 
@dataclass 
class GetStudentPaymentHistoryCommand: 
    student_id: UUID 
    page: int = 0 
    size: int = 20 
 
 
@dataclass 
class GetStudentPaymentHistoryResult: 
    student_id: UUID 
    payments: list[StudentPayment] 
 
 
class GetStudentPaymentHistoryUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
 
    def execute( 
        self, command: GetStudentPaymentHistoryCommand 
    ) -> GetStudentPaymentHistoryResult: 
 
        payments = self.student_payment_repository.find_by_student( 
            student_id=command.student_id, 
            page=command.page, 
            size=command.size, 
        ) 
 
        return GetStudentPaymentHistoryResult( 
            student_id=command.student_id, 
            payments=payments, 
        ) 