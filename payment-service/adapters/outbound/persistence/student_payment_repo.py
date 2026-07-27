from uuid import UUID
from typing import Optional 
from datetime import datetime, timezone

from domain.models import StudentPayment
from domain.enums import StudentPaymentStatus
from application.ports.outbound.student_payment__repository import StudentPaymentRepositoryPort
from core.models import StudentPaymentModel


class DjangoStudentPaymentRepository(StudentPaymentRepositoryPort):
    
    # mapping
    
    def _to_domain(self, orm: StudentPaymentModel) -> StudentPayment:
        return StudentPayment(
            id=orm.id,
            student_id=orm.student_id,
            payment_month=orm.payment_month,
            amount=orm.amount, 
            currency=orm.currency,
            status=StudentPaymentStatus(orm.status),
            reference_number=orm.reference_number,
            note=orm.note,
            verified_by=orm.verified_by,
            verified_at=orm.verified_at,
            due_date=orm.due_date,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
    
    def _to_orm_fields(self, payment: StudentPayment) -> dict:
        return {
            "student_id": payment.student_id,
            "payment_month": payment.payment_month,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "reference_number": payment.reference_number,
            "note": payment.note,
            "verified_by": payment.verified_by,
            "verified_at": payment.verified_at,
            "due_date": payment.due_date
        }
        
    # port implementation
    
    def save(self, payment: StudentPayment) -> StudentPayment:
        orm, _ = StudentPaymentModel.objects.update_or_create(id=payment.id, defaults=self._to_orm_fields(payment),)

        return self._to_domain(orm)
    
    def find_by_id(self, payment_id: UUID) -> Optional[StudentPayment]:
        try:
            return self._to_domain(
                StudentPaymentModel.objects.get(id=payment_id)
            )
        except StudentPaymentModel.DoesNotExist:
            return None
        