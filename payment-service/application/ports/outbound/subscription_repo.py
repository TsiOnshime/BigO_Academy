from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from domain.enums import SubscriptionStatus
from domain.models import Subscription


class SubscriptionRepositoryPort(ABC):

    @abstractmethod
    def save(self, subscription: Subscription) -> Subscription:
        """Insert or update a subscription."""
        ...

    @abstractmethod
    def find_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        ...

    @abstractmethod
    def find_by_student(
        self, student_id: UUID, status: Optional[SubscriptionStatus] = None
    ) -> list[Subscription]:
        ...

    @abstractmethod
    def find_active_by_student_and_plan(
        self, student_id: UUID, plan_id: UUID
    ) -> Optional[Subscription]:
        """Used to enforce StudentAlreadySubscribedError — finds an
        ACTIVE or PAST_DUE subscription for this student+plan pair, if any."""
        ...

    @abstractmethod
    def find_all(self, status: Optional[SubscriptionStatus] = None) -> list[Subscription]:
        ...

    @abstractmethod
    def find_expiring(self, as_of: date) -> list[Subscription]:
        """Subscriptions whose current_period_end has passed (<= as_of)
        and are still ACTIVE or PAST_DUE — candidates for a renewal or
        expiry job to process."""
        ...