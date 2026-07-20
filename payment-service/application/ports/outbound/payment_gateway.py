from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class GatewayResult:
    """
    Shared result shape for every PaymentGatewayPort operation — charging
    a student, refunding a transaction, or paying out a teacher all boil
    down to the same three facts: did it work, what's the provider's own
    reference for it (for reconciliation/idempotency), and if it failed,
    why.
    """

    success: bool
    provider_reference: Optional[str]
    error_message: Optional[str] = None


class PaymentGatewayPort(ABC):
    """
    Interface to the real payment provider (e.g. Stripe, Chapa). The
    concrete adapter — and which provider it wraps — is intentionally not
    decided in this pass; this interface just defines the shape any
    provider adapter must satisfy so the use cases in application/ can be
    written and tested (via a fake) before that decision is made.
    """

    @abstractmethod
    def charge(
        self, student_id: UUID, amount: float, currency: str, reference: str
    ) -> GatewayResult:
        """Charge a student for an invoice. `reference` is our own
        idempotency key (e.g. the invoice id as a string) so retries
        don't double-charge."""
        ...

    @abstractmethod
    def refund(
        self, original_provider_reference: str, amount: float, currency: str
    ) -> GatewayResult:
        """Refund a previously completed charge, identified by the
        provider_reference returned from the original charge()."""
        ...

    @abstractmethod
    def payout(
        self, teacher_id: UUID, amount: float, currency: str, reference: str
    ) -> GatewayResult:
        """Pay out a teacher. `reference` is our own idempotency key (e.g.
        the payout id as a string)."""
        ...