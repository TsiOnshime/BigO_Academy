from dataclasses import dataclass 
 
from domain.models import StudentPayment 
from domain.enums import StudentPaymentStatus 
from application.ports.outbound.student_payment_repository import StudentPaymentRepositoryPort 
 
 
@dataclass 
class ListPendingVerificationCommand: 
    page: int = 0 
    size: int = 20 
 
 
class ListPendingVerificationUseCase: 
 
    def __init__( 
        self, 
        student_payment_repository: StudentPaymentRepositoryPort, 
    ): 
        self.student_payment_repository = student_payment_repository 
 
    def execute( 
        self, command: ListPendingVerificationCommand 
    ) -> list[StudentPayment]: 
 
        return self.student_payment_repository.find_by_status( 
            status=StudentPaymentStatus.PENDING, 
            page=command.page, 
            size=command.size, 
        ) 