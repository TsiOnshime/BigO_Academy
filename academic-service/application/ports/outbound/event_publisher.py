from abc import ABC, abstractmethod
from uuid import UUID



from domain.models import (Student, Teacher, Cohort, Contest, ContestResult, Warning,)

class EventPublisherPort(ABC):
    """Abstract contract for publishing academic domain events to Kafka. Consumed by Analytics Service to update rankings, metrics, and reports. Implemented by KafkaEventPublisher in adapters/outbound/messaging/."""
    
    # Student Events
    
    @abstractmethod
    def publish_student_created(self, student: Student) -> None:
        """Published when: admin creates a student profile."""
    
    @abstractmethod
    def publish_student_status_changed(self, student: Student, old_status: str) -> None:
        """Published when: admin changes student status."""
    @abstractmethod
    def publish_student_promoted(self, student: Student) -> None:
        """Published when: admin promotes student from Year1 to Year2"""
    @abstractmethod
    def publish_student_graduated(self, student: Student) -> None:
        """Published when: admin marks student as graduated"""
    @abstractmethod
    def publish_student_dropped(self, student: Student) -> None:
        """Published when: admin drops student from program"""
    
    # Teacher Events
    
    @abstractmethod
    def publish_teacher_created(self, teacher: Teacher) -> None:
        """Published when: admin creates a teacher profile."""
    
    @abstractmethod
    def publish_teacher_status_changed(self, teacher: Teacher) -> None:
        """Published when: admin activates or deactivates a teacher"""
    @abstractmethod
    def publish_teacher_assigned_to_cohort(self, teacher_id: UUID, cohort_id: UUID) -> None:
        """Published when: admin assigns teacher to cohort."""
    @abstractmethod
    def publish_teacher_unassigned_from_cohort(self, teacher_id: UUID, cohort_id: UUID) -> None:
        """Published when: admin removes teacher from cohort"""
    # Cohort Events
    @abstractmethod
    def publish_cohort_created(self, cohort: Cohort) -> None:
        """Published when: admin creates a new cohort"""
    @abstractmethod
    def publish_cohort_updated(self, cohort: Cohort) -> None:
        """Published when: admin updates cohort details"""
    @abstractmethod
    def publish_cohort_archived(self, cohort: Cohort) -> None:
        """Published when: admin archives a completed cohort"""
        
    # Academic Activity Events
    @abstractmethod
    def publish_problem_solved(self,student_id: UUID,problem_id: UUID, attempts: int,solve_time_minutes: int) -> None:
        """
        Published when: student marks a problem as solved.
        Analytics uses this to update consistency score,
        performance score, and rankings.
        """
        

    @abstractmethod
    def publish_attendance_updated(self, student_id: UUID,session_id: UUID, status: str) -> None:
        """
        Published when: teacher submits or edits attendance.
        Analytics uses this to update attendance metrics
        and performance score.
        """
        
    @abstractmethod
    def publish_contest_finished(self,contest_id: UUID,cohort_id: UUID,results: list[ContestResult]) -> None:
        """
        Published when: teacher submits contest results.
        Analytics uses this to update contest ratings and rankings.
        """
        ...

    # Warning Events 

    @abstractmethod
    def publish_warning_issued(self, warning: Warning) -> None:
        """
        Published when: system generates a new warning.
        Analytics uses this to update warning statistics
        and at-risk indicators.
        """
        ...

    @abstractmethod
    def publish_warning_resolved(self, warning: Warning) -> None:
        """
        Published when: teacher or admin dismisses a warning.
        Analytics uses this to update improvement metrics.
        """