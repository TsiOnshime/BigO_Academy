from dataclasses import dataclass 
from typing import Optional 
 
from domain.models import TeacherPayment 
from domain.enums import TeacherPaymentStatus 
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort 
 
 
@dataclass 
class GetTeacherPaymentReportCommand: 
    status: Optional[TeacherPaymentStatus] = None 
    month: Optional[str] = None 
    page: int = 0 
    size: int = 20 
 
 
@dataclass 
class GetTeacherPaymentReportResult: 
    payments: list[TeacherPayment] 
    month: Optional[str] 
 
 
class GetTeacherPaymentReportUseCase: 
 
    def __init__( 
        self, 
        teacher_payment_repository: TeacherPaymentRepositoryPort, 
    ): 
        self.teacher_payment_repository = teacher_payment_repository 
 
    def execute( 
        self, command: GetTeacherPaymentReportCommand 
    ) -> GetTeacherPaymentReportResult: 
 
        if command.month is not None: 
            payments = self.teacher_payment_repository.find_by_month( 
                command.month 
            ) 
            if command.status is not None: 
                payments = [ 
                    p for p in payments if p.status == command.status 
                ] 
        elif command.status is not None: 
            payments = self.teacher_payment_repository.find_by_status( 
                status=command.status, 
                page=command.page, 
                size=command.size, 
            ) 
        else: 
            payments = ( 
                self.teacher_payment_repository.find_by_status( 
                    TeacherPaymentStatus.PENDING 
                ) + self.teacher_payment_repository.find_by_status( 
                    TeacherPaymentStatus.PAID 
                ) 
            ) 
 
        return GetTeacherPaymentReportResult( 
            payments=payments, 
            month=command.month, 
        ) 