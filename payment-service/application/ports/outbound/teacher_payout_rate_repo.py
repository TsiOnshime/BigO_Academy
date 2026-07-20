from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from domain.models import TeacherPayoutRate


class TeacherPayoutRateRepositoryPort(ABC):

    @abstractmethod
    def save(self, rate: TeacherPayoutRate) -> TeacherPayoutRate:
        """Insert a new rate record. Rates are append-only (a new
        effective_from row, not an update-in-place) so payout history
        computed against past periods stays accurate even after a
        teacher's rate changes."""
        ...

    @abstractmethod
    def find_current_by_teacher(
        self, teacher_id: UUID, as_of: date
    ) -> Optional[TeacherPayoutRate]:
        """The rate in effect on the given date — the row with the latest
        effective_from that is <= as_of."""
        ...

    @abstractmethod
    def find_all_by_teacher(self, teacher_id: UUID) -> list[TeacherPayoutRate]:
        """Full rate history for a teacher, for audit/display purposes."""
        ...