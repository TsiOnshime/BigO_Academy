from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from domain.enums import InvoiceStatus
from domain.models import Invoice


class InvoiceRepositoryPort(ABC):

    @abstractmethod
    def save(self, invoice: Invoice) -> Invoice:
        """Insert or update an invoice, including its line items."""
        ...

    @abstractmethod
    def find_by_id(self, invoice_id: UUID) -> Optional[Invoice]:
        ...

    @abstractmethod
    def find_by_student(
        self, student_id: UUID, status: Optional[InvoiceStatus] = None
    ) -> list[Invoice]:
        ...

    @abstractmethod
    def find_by_subscription(self, subscription_id: UUID) -> list[Invoice]:
        ...

    @abstractmethod
    def find_overdue(self, as_of: date) -> list[Invoice]:
        """Invoices with status=ISSUED whose due_at has passed as of the
        given date — candidates for an OVERDUE-marking job."""
        ...