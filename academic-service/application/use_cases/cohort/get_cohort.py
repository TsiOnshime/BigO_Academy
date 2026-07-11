from dataclasses import dataclass
from uuid import UUID

from domain.models import Cohort
from domain.exceptions import CohortNotFoundError
from application.ports.outbound.cohort_repository import CohortRepositoryPort


@dataclass
class GetCohortCommand:
    cohort_id: UUID


class GetCohortUseCase:

    def __init__(self, cohort_repository: CohortRepositoryPort):
        self.cohort_repository = cohort_repository

    def execute(self, command: GetCohortCommand) -> Cohort:

        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))

        return cohort