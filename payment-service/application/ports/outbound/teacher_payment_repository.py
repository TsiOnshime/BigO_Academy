from abc import ABC, abstractmethod 
from uuid import UUID 
from typing import Optional 
 
from domain.models import TeacherPayment 
from domain.enums import TeacherPaymentStatus 
 
 
class TeacherPaymentRepositoryPort(ABC): 
 
    @abstractmethod 
    def save(self, payment: TeacherPayment) -> TeacherPayment: 
        """Insert or update a teacher payment.""" 
        ... 
 
    @abstractmethod 
    def find_by_id(self, payment_id: UUID) -> Optional[TeacherPayment]: 
        """Fetch by UUID. Returns None if not found.""" 
        ... 
 
    @abstractmethod 
    def find_by_teacher( 
        self, 
        teacher_id: UUID, 
        page: int = 0, 
        size: int = 20, 
    ) -> list[TeacherPayment]: 
        """Return all payment records for a teacher. Most recent first.""" 
        ... 
 
    @abstractmethod 
    def find_by_status( 
        self, 
        status: TeacherPaymentStatus, 
        page: int = 0, 
        size: int = 20, 
    ) -> list[TeacherPayment]: 
        """ 
        List teacher payments filtered by status. 
        Used by admin to see pending teacher payments. 
        """ 
        ... 
 
    @abstractmethod 
    def find_by_month( 
        self, 
        payment_month: str, 
    ) -> list[TeacherPayment]: 
        """ 
        Return all teacher payments for a specific month. 
        Used for monthly payment reports. 
        """ 