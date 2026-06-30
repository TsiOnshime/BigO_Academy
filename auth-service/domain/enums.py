from enum import Enum

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"

class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class OAuthProvider(str, Enum):
    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"