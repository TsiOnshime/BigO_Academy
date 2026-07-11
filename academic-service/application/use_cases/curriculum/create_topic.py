from dataclasses import dataclass
from uuid import UUID, uuid4
from typing import Optional

from domain.enums import YearPhase
from domain.models import Topic
from domain.exceptions import CohortNotFoundError
from application.ports.outbound.curriculum_repository import CurriculumRepositoryPort
from application.ports.outbound.cohort_repository import CohortRepositoryPort

@dataclass
class CreateTopicCommand:
    cohort_id: UUID
    title: str
    year_phase: YearPhase
    description: Optional[str] = None
    display_order: Optional[int] = None
    
class CreateTopicUseCase:
    def __init__(self, curriculum_repository: CurriculumRepositoryPort, cohort_repository: CohortRepositoryPort):
        self.curriculum_repository = curriculum_repository
        self.cohort_repository = cohort_repository
    
    def execute(self, command: CreateTopicCommand) -> Topic:
        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.id))
        
        new_topic = Topic(
            id=uuid4(),
            curriculum_id=command.cohort_id,
            title=command.title,
            description=command.description, 
            year_phase=command.year_phase,
            display_order=command.display_order or 0,
            problem_count=0,
            
        )
        
        return self.curriculum_repository.save_topic(new_topic)