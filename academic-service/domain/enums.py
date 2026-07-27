from enum import Enum


class StudentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PROBATION = "PROBATION"
    DROPPED = "DROPPED"
    GRADUATED = "GRADUATED"
    ARCHIVED = "ARCHIVED"

class TeacherStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class CohortStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    EXCUSED = "EXCUSED"

class ContestStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"

class WarningStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISMISSED = "DISMISSED"
    ESCALATED = "ESCALATED"

class WarningType(str, Enum):
    LOW_ATTENDANCE = "LOW_ATTENDANCE"
    LOW_PERFORMANCE = "LOW_PERFORMANCE"
    LOW_CONSISTENCY = "LOW_CONSISTENCY"
    WEAK_CONTEST_PARTICIPATION = "WEAK_CONTEST_PARTICIPATION"

class ProblemSource(str, Enum):
    LEETCODE = "LEETCODE"
    CODEFORCES = "CODEFORCES"

class ProblemDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class MentorshipSessionStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class YearPhase(int, Enum):
    YEAR_ONE = 1
    YEAR_TWO = 2    
