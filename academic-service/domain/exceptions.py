class DomainError(Exception):
    """Base class for all domain-level errors in the Academic Service."""
    
    pass


# Not Found Errors


class StudentNotFoundError(DomainError):
    def __init__(self, student_id: str):
        self.student_id = student_id
        super().__init__(f"Student not found: {student_id}")
class TeacherNotFoundError(DomainError):
    def __init__(self, teacher_id: str):
        self.teacher_id = teacher_id
        super().__init__(f"Teacher not found: {teacher_id}")
class CohortNotFoundError(DomainError):
    def __init__(self, cohort_id: str):
        self.cohort_id = cohort_id
        super().__init__(f"Cohort not found: {cohort_id}")
        
class TopicNotFoundError(DomainError):
    def __init__(self, topic_id: str):
        self.topic_id = topic_id
        super().__init__(f"Topic not found: {topic_id}")
        
class ProblemNotFoundError(DomainError):
    def __init__(self, problem_id: str):
        self.problem_id = problem_id
        super().__init__(f"Problem not found: {problem_id}")
        
class ContestNotFoundError(DomainError):
    def __init__(self, contest_id: str):
        self.contest_id = contest_id
        super().__init__(f"Contest not found: {contest_id}")

class SessionNotFoundError(DomainError):
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")

class MentorshipNotFoundError(DomainError):
    def __init__(self, mentorship_id: str):
        self.mentorship_id = mentorship_id
        super().__init__(f"Mentorship not found: {mentorship_id}")
        
class WarningNotFoundError(DomainError):
    def __init__(self, warning_id: str):
        self.warning_id = warning_id
        super().__init__(f"Cohort not found: {warning_id}")
        
        
# Conflict Errors

class StudentAlreadyExistsError(DomainError):
    '''Raised when creating a student profile that already exists.'''
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"Student profile already exists for user: {user_id}")
    
class TeacherAlreadyExistsError(DomainError):
    '''Raised when creating a teacher profile that already exists'''
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"Teacher profile already exists for user: {user_id}")
        
class StudentAlreadyInCohortError(DomainError):
    '''Raised when assigning a student to a cohort they're already in.'''
    def __init__(self, student_id: str, cohort_id: str):
        self.student_id = student_id
        self.cohort_id = cohort_id
        super().__init__(
            f"Student {student_id} is already assigned to cohort {cohort_id}"
        )
class TeacherAlreadyInCohortError(DomainError):
    '''Raised when assigning a teacher to a cohort they're already in.'''
    def __init__(self, teacher_id: str, cohort_id: str):
        self.teacher_id = teacher_id
        self.cohort_id = cohort_id
        super().__init__(f"Teacher {teacher_id} is already assigned to cohort {cohort_id}")
        
class ContestResultsAlreadySubmittedError(DomainError):
    '''Raised when submitting results for a contest that already has results'''
    def __init__(self, contest_id: str):
        self.contest_id = contest_id
        super().__init__(f"Results already submitted for contest: {contest_id}")
        
# ── Invalid State Transition Errors ──────────────────────────────────────

class InvalidStudentStatusTransitionError(DomainError):
    """
    Raised when attempting an invalid student status transition.
    Valid transitions per spec:
    ACTIVE → PROBATION
    PROBATION → DROPPED
    ACTIVE → GRADUATED
    Any → ARCHIVED
    """
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid status transition: {current_status} → {target_status}"
        )
class StudentNotEligibleForPromotionError(DomainError):
    """
    Raised when trying to promote a student who is not in Year 1
    or is not in ACTIVE status.
    """
    def __init__(self, student_id: str, reason: str):
        self.student_id = student_id
        self.reason = reason
        super().__init__(
            f"Student {student_id} is not eligible for promotion: {reason}"
        )
        
class StudentNotEligibleForGraduationError(DomainError):
    """
    Raised when trying to graduate a student who hasn't completed Year 2
    or is not in ACTIVE status.
    """
    def __init__(self, student_id: str, reason: str):
        self.student_id = student_id
        self.reason = reason
        super().__init__(
            f"Student {student_id} is not eligible for graduation: {reason}"
        )
class CohortArchivedError(DomainError):
    """
    Raised when trying to perform operations on an archived cohort
    that are only valid for active cohorts.
    """
    def __init__(self, cohort_id: str):
        self.cohort_id = cohort_id
        super().__init__(f"Cohort {cohort_id} is archived and cannot be modified")
class ContestNotFinishedError(DomainError):
    """
    Raised when trying to submit results for a contest
    that hasn't finished yet.
    """
    def __init__(self, contest_id: str):
        self.contest_id = contest_id
        super().__init__(
            f"Contest {contest_id} has not finished yet — results cannot be submitted"
        )
# ── Permission Errors ─────────────────────────────────────────────────────

class UnauthorizedAccessError(DomainError):
    """
    Raised when a user tries to access a resource they don't have
    permission for — e.g. a teacher accessing a student not in their cohort.
    """
    def __init__(self, reason: str = "You do not have permission to access this resource"):
        super().__init__(reason)

# ── Warning Errors ────────────────────────────────────────────────────────

class WarningAlreadyDismissedError(DomainError):
    """Raised when trying to dismiss a warning that's already dismissed."""
    def __init__(self, warning_id: str):
        self.warning_id = warning_id
        super().__init__(f"Warning {warning_id} has already been dismissed")