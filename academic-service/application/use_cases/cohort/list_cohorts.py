from dataclasses import dataclass
from typing import Optional

from domain.models import Cohort
from domain.enums import CohortStatus
from application.ports.outbound.cohort_repository import CohortRepositoryPort


@dataclass
class ListCohortsCommand:
    status: Optional[CohortStatus] = None


class ListCohortsUseCase:

    def __init__(self, cohort_repository: CohortRepositoryPort):
        self.cohort_repository = cohort_repository

    def execute(self, command: ListCohortsCommand) -> list[Cohort]:
        return self.cohort_repository.find_all(status=command.status)