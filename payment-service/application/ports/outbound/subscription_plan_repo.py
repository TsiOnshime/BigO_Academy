from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from domain.models import SubscriptionPlan


class SubscriptionPlanRepositoryPort(ABC):

    @abstractmethod
    def save(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        """Insert or update a subscription plan."""
        ...

    @abstractmethod
    def find_by_id(self, plan_id: UUID) -> Optional[SubscriptionPlan]:
        ...

    @abstractmethod
    def find_all(self, active_only: Optional[bool] = None) -> list[SubscriptionPlan]:
        """List plans, optionally filtered to only is_active=True plans."""
        ...