from abc import ABC, abstractmethod 
from uuid import UUID 
from typing import Optional 
 
from domain.models import StudentPayment 
from domain.enums import StudentPaymentStatus 
 
 
class StudentPaymentRepositoryPort(ABC): 
 
    @abstractmethod 
    def save(self, payment: StudentPayment) -> StudentPayment: 
        """Insert or update a student payment. Returns the saved payment.""" 
        ... 
 
    @abstractmethod 
    def find_by_id(self, payment_id: UUID) -> Optional[StudentPayment]: 
        """Fetch by UUID. Returns None if not found.""" 
        ... 
 
    @abstractmethod 
    def find_by_student( 
        self, 
        student_id: UUID, 
        page: int = 0, 
        size: int = 20, 
    ) -> list[StudentPayment]: 
        """ 
        Return all payment records for a student. 
        Paginated — most recent first. 
        """ 
        ... 
 
    @abstractmethod 
    def find_by_student_and_month( 
        self, 
        student_id: UUID, 
        payment_month: str, 
    ) -> Optional[StudentPayment]: 
        """ 
        Find a specific payment record for a student and month. 
        Used to detect duplicate payments before creating a new one. 
        """ 
        ... 
 
    @abstractmethod 
    def find_by_status( 
        self, 
        status: StudentPaymentStatus, 
        cohort_id: Optional[UUID] = None, 
        page: int = 0, 
        size: int = 20, 
    ) -> list[StudentPayment]: 
        """ 
        List payments filtered by status. 
        Used by: 
        - Admin to see pending verifications (status=PENDING) 
        - Admin to see overdue subscriptions (status=OVERDUE) 
        Optional cohort_id filter for scoping to a specific cohort. 
        Note: cohort_id is stored on the payment record — the Payment 
        Service receives it from the Academic Service via Kafka when 
        a student is assigned to a cohort. 
        """ 
        ... 
 
    @abstractmethod 
    def find_overdue(self) -> list[StudentPayment]: 
        """ 
        Return all payments that are past their due_date 
        and still PENDING. Used by the scheduled job to 
        mark them as OVERDUE. 
        """ 