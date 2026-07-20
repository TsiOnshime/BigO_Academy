from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from domain.enums import PayoutStatus
from domain.models import TeacherPayout


class TeacherPayoutRepositoryPort(ABC):

    @abstractmethod
    def save(self, payout: TeacherPayout) -> TeacherPayout:
        """Insert or update a payout."""
        ...

    @abstractmethod
    def find_by_id(self, payout_id: UUID) -> Optional[TeacherPayout]:
        ...

    @abstractmethod
    def find_by_teacher(self, teacher_id: UUID) -> list[TeacherPayout]:
        ...

    @abstractmethod
    def find_by_teacher_and_period(
        self, teacher_id: UUID, period_start: date, period_end: date
    ) -> Optional[TeacherPayout]:
        """Used to enforce PayoutPeriodAlreadyComputedError."""
        ...

    @abstractmethod
    def find_all(self, status: Optional[PayoutStatus] = None) -> list[TeacherPayout]:
        ...