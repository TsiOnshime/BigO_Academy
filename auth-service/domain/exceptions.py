class DomainError(Exception):
    """base class for all domain level errors in the auth service"""
    pass

class EmailAlreadyExistsError(DomainError):
    def __init__(self, email:str):
        """raised when registering with an already existing email"""
        self.email = email
        super().__init__(f"An account with email {email} already exists")
    
class InvalidCredentialsError(DomainError):
    def __init__(self):
        """raised when incorrect password or email is used"""
        super().__init__("Invalid email or password")
        
class AccountInactiveError(DomainError):
    def __init__(self):
        """raised when trying to login to a deactivated account"""
        super().__init__("Your account has been deactivated. Contact an administrator.")
        
class InvalidTokenError(DomainError):
    """raised when a refresh token, reset token, or access token is invalid or expired"""
    def __init__(self, message: str = "Token is invalid or expired"):
        super().__init__(message)
        
class InvalidOtpError(DomainError):
    """raised when OTP code is incorrect or has expired."""
    def __init__(self):
        super().__init__("OTP is invalid or has expired")
        
class IncorrectPasswordError(DomainError):
    """raised when a user's current password doesn't match during change-password"""
    def __init__(self):
        super().__init__("Current is incorrect")
        
class UserNotFoundError(DomainError):
    """Raised when looking up a user by id or email that doesn't exist."""
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Account not found: {identifier}")
        
class PasswordMismatchError(DomainError):
    """raised when passoword and confirmPassword doesn't match during registration or reset"""
    
    def __init__(self):
        super().__init__("Password do not match")
        