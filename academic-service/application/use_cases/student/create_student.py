from dataclasses import dataclass
from datetime import date

from uuid import uuid4, UUID

from domain.models import Student
from domain.exceptions import StudentAlreadyExistsError, CohortNotFoundError, CohortArchivedError
from domain.enums import YearPhase, StudentStatus
from application.ports.outbound.student_repository import StudentRepositoryPort
from application.ports.outbound.event_publisher import EventPublisherPort
from application.ports.outbound.cohort_repository import CohortRepositoryPort

@dataclass
class CreateStudentCommand:
    user_id: UUID
    full_name: str
    email: str
    cohort_id: UUID
    joined_at: date

@dataclass
class CreateStudentResult:
    student: Student
    
class CreateStudentUseCase:
    def __init__(self, student_repository: StudentRepositoryPort, cohort_repository: CohortRepositoryPort, event_publisher: EventPublisherPort):
        self.student_repository = student_repository
        self.cohort_repository = cohort_repository
        self.event_publisher = event_publisher
        
    def execute(self, command: CreateStudentCommand) -> CreateStudentResult:
        if self.student_repository.exists_by_user_id(command.user_id):
            raise StudentAlreadyExistsError(str(command.user_id))
        cohort = self.cohort_repository.find_by_id(command.cohort_id)
        if cohort is None:
            raise CohortNotFoundError(str(command.cohort_id))
        
        if not cohort.is_active():
            raise CohortArchivedError(str(command.cohort_id))
        
        new_student = Student(
            id=uuid4(),
            user_id=command.user_id,
            full_name=command.full_name,
            email=command.email,
            cohort_id=command.cohort_id,
            year_phase=YearPhase.YEAR_ONE,
            status=StudentStatus.ACTIVE,
            assigned_teacher_id=None,
            attendance_percentage=0.0,
            active_warning_count=0,
            joined_at=command.joined_at,
        )
        
        saved_student = self.student_repository.save(new_student)
        
        self.cohort_repository.assign_student(command.cohort_id, saved_student.id)
        
        self.event_publisher.publish_student_created(saved_student)
        
        return CreateStudentResult(student=saved_student)