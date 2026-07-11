from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from domain.models import Warning
from application.ports.outbound.warning_repository import WarningRepositoryPort


@dataclass
class ListEscalatedWarningsCommand:
    cohort_id: Optional[UUID] = None


class ListEscalatedWarningsUseCase:

    def __init__(self, warning_repository: WarningRepositoryPort):
        self.warning_repository = warning_repository

    def execute(
        self, command: ListEscalatedWarningsCommand
    ) -> list[Warning]:
        return self.warning_repository.find_escalated(
            cohort_id=command.cohort_id
        )