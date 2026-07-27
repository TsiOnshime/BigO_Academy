from dataclasses import dataclass 
 
from domain.models import TeacherPayment 
from domain.enums import TeacherPaymentStatus 
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort 
 
 
@dataclass 
class ListPendingTeacherPaymentsCommand: 
    page: int = 0 
    size: int = 20 
 
 
class ListPendingTeacherPaymentsUseCase: 
 
    def __init__( 
        self, 
        teacher_payment_repository: TeacherPaymentRepositoryPort, 
    ): 
        self.teacher_payment_repository = teacher_payment_repository 
 
    def execute( 
        self, command: ListPendingTeacherPaymentsCommand 
    ) -> list[TeacherPayment]: 
 
        return self.teacher_payment_repository.find_by_status( 
            status=TeacherPaymentStatus.PENDING, 
            page=command.page, 
            size=command.size, 
        ) 