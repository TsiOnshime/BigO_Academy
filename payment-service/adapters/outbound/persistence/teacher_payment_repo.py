from uuid import UUID
from typing import Optional

from domain.models import TeacherPayment
from domain.enums import TeacherPaymentStatus
from application.ports.outbound.teacher_payment_repository import TeacherPaymentRepositoryPort
from core.models import TeacherPaymentModel


class DjangoTeacherPaymentRepository(TeacherPaymentRepositoryPort):

    def _to_domain(self, orm: TeacherPaymentModel) -> TeacherPayment:
        return TeacherPayment(
            id=orm.id,
            teacher_id=orm.teacher_id,
            payment_month=orm.payment_month,
            amount=orm.amount,
            currency=orm.currency,
            status=TeacherPaymentStatus(orm.status),
            note=orm.note,
            processed_by=orm.processed_by,
            processed_at=orm.processed_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm_fields(self, payment: TeacherPayment) -> dict:
        return {
            "teacher_id": payment.teacher_id,
            "payment_month": payment.payment_month,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "note": payment.note,
            "processed_by": payment.processed_by,
            "processed_at": payment.processed_at,
        }

    def save(self, payment: TeacherPayment) -> TeacherPayment:
        orm, _ = TeacherPaymentModel.objects.update_or_create(
            id=payment.id,
            defaults=self._to_orm_fields(payment),
        )
        return self._to_domain(orm)

    def find_by_id(self, payment_id: UUID) -> Optional[TeacherPayment]:
        try:
            return self._to_domain(
                TeacherPaymentModel.objects.get(id=payment_id)
            )
        except TeacherPaymentModel.DoesNotExist:
            return None

    def find_by_teacher(
        self,
        teacher_id: UUID,
        page: int = 0,
        size: int = 20,
    ) -> list[TeacherPayment]:
        offset = page * size
        queryset = TeacherPaymentModel.objects.filter(
            teacher_id=teacher_id
        ).order_by("-created_at")[offset:offset + size]
        return [self._to_domain(orm) for orm in queryset]

    def find_by_status(
        self,
        status: TeacherPaymentStatus,
        page: int = 0,
        size: int = 20,
    ) -> list[TeacherPayment]:
        offset = page * size
        queryset = TeacherPaymentModel.objects.filter(
            status=status.value
        ).order_by("-created_at")[offset:offset + size]
        return [self._to_domain(orm) for orm in queryset]

    def find_by_month(self, payment_month: str) -> list[TeacherPayment]:
        queryset = TeacherPaymentModel.objects.filter(
            payment_month=payment_month
        ).order_by("-created_at")
        return [self._to_domain(orm) for orm in queryset]