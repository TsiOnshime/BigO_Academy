from abc import ABC, abstractmethod

from domain.models import Invoice, Subscription, TeacherPayout, Transaction


class EventPublisherPort(ABC):
    """
    Outbound events published to Kafka once the adapters layer exists.
    Method shape follows academic-service's EventPublisherPort: pass the
    full domain entity where one exists, rather than loose primitive
    fields, so the adapter has everything it needs to build the payload.
    """

    # ── Subscription Events ─────────────────────────────────────────────

    @abstractmethod
    def publish_subscription_created(self, subscription: Subscription) -> None:
        ...

    @abstractmethod
    def publish_subscription_status_changed(
        self, subscription: Subscription, old_status: str
    ) -> None:
        ...

    @abstractmethod
    def publish_subscription_cancelled(self, subscription: Subscription) -> None:
        ...

    # ── Invoice Events ───────────────────────────────────────────────────

    @abstractmethod
    def publish_invoice_issued(self, invoice: Invoice) -> None:
        ...

    @abstractmethod
    def publish_invoice_paid(self, invoice: Invoice) -> None:
        ...

    @abstractmethod
    def publish_invoice_overdue(self, invoice: Invoice) -> None:
        ...

    # ── Transaction Events ───────────────────────────────────────────────

    @abstractmethod
    def publish_transaction_completed(self, transaction: Transaction) -> None:
        ...

    @abstractmethod
    def publish_transaction_failed(self, transaction: Transaction) -> None:
        ...

    @abstractmethod
    def publish_transaction_reversed(self, transaction: Transaction) -> None:
        ...

    # ── Payout Events ────────────────────────────────────────────────────

    @abstractmethod
    def publish_payout_approved(self, payout: TeacherPayout) -> None:
        ...

    @abstractmethod
    def publish_payout_paid(self, payout: TeacherPayout) -> None:
        ...

    @abstractmethod
    def publish_payout_failed(self, payout: TeacherPayout) -> None:
        ...