from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import uuid4

from domain.models import Cohort
from domain.enums import CohortStatus
from application.ports.outbound.cohort_repository import CohortRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort

@dataclass
class CreateCohortCommand:
    name: str
    start_date: date
    expected_graduation_date: date
    student_capacity: int
    intake_window_one: Optional[date] = None
    intake_window_two: Optional[date] = None
    

@dataclass
class CreateCohortResult:
    cohort: Cohort
    
class CreateCohortUseCase:
    def __init__(self, cohort_repository: CohortRepositoryPort, event_publisher: EventPublisherPort):
        self.cohort_repository = cohort_repository
        self.event_publisher = event_publisher
    def execute(self, command: CreateCohortCommand) -> CreateCohortResult:
        new_cohort = Cohort(
            id=uuid4(),
            name=command.name, 
            status=CohortStatus.ACTIVE, 
            intake_window_one=command.intake_window_one,
            intake_window_two=command.intake_window_two,
            start_date=command.start_date,
            expected_graduation_date=command.expected_graduation_date,
            student_capacity=command.student_capacity,
            enrolled_student_count=0,
            teacher_count=0
        )
        
        saved_cohort = self.cohort_repository.save(new_cohort)
        self.event_publisher.publish_cohort_created(saved_cohort)
        
        return CreateCohortResult(cohort=saved_cohort)
    