from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from domain.enums import TransactionType
from domain.models import Transaction


class TransactionRepositoryPort(ABC):

    @abstractmethod
    def save(self, transaction: Transaction) -> Transaction:
        """Insert or update a transaction."""
        ...

    @abstractmethod
    def find_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        ...

    @abstractmethod
    def find_by_invoice(self, invoice_id: UUID) -> list[Transaction]:
        ...

    @abstractmethod
    def find_by_payout(self, payout_id: UUID) -> list[Transaction]:
        ...

    @abstractmethod
    def find_by_student(
        self, student_id: UUID, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[Transaction]:
        ...

    @abstractmethod
    def find_by_teacher(
        self, teacher_id: UUID, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> list[Transaction]:
        ...

    @abstractmethod
    def sum_completed_amount(
        self,
        transaction_type: TransactionType,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> float:
        """Sum of amount for COMPLETED transactions of the given type in
        the date range — the building block financial reporting use cases
        (revenue summary, payouts-paid summary) aggregate on top of."""
        ...