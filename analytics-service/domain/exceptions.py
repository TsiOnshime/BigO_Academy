class DomainError(Exception):
    pass

class StudentAnalyticsNotFoundError(DomainError):
    def __init__(self, student_id: str):
        self.student_id = student_id
        super().__init__(f"Student analytics not found: {student_id}")

class CohortAnalyticsNotFoundError(DomainError):
    def __init__(self, cohort_id: str):
        self.cohort_id = cohort_id
        super().__init__(f"Cohort analytics not found: {cohort_id}")

class TeacherAnalyticsNotFoundError(DomainError):
    def __init__(self, teacher_id: str):
        self.teacher_id = teacher_id
        super().__init__(f"Teacher analytics not found: {teacher_id}")