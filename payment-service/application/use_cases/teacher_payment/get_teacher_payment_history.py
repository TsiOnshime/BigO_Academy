from dataclasses import dataclass 
from uuid import UUID 
 
from domain.models import TeacherPayment 
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort 
 
 
@dataclass 
class GetTeacherPaymentHistoryCommand: 
    teacher_id: UUID 
    page: int = 0 
    size: int = 20 
 
 
@dataclass 
class GetTeacherPaymentHistoryResult: 
    teacher_id: UUID 
    payments: list[TeacherPayment] 
 
 
class GetTeacherPaymentHistoryUseCase: 
 
    def __init__( 
        self, 
        teacher_payment_repository: TeacherPaymentRepositoryPort, 
    ): 
        self.teacher_payment_repository = teacher_payment_repository 
 
    def execute( 
        self, command: GetTeacherPaymentHistoryCommand 
    ) -> GetTeacherPaymentHistoryResult: 
 
        payments = self.teacher_payment_repository.find_by_teacher( 
            teacher_id=command.teacher_id, 
            page=command.page, 
            size=command.size, 
        ) 
 
        return GetTeacherPaymentHistoryResult( 
            teacher_id=command.teacher_id, 
            payments=payments, 
        ) 