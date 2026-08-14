import secrets
import string
from dataclasses import dataclass

from domain.enums import UserRole, AccountStatus
from domain.models import User
from domain.exceptions import EmailAlreadyExistsError

from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.password_hasher import PasswordHasherPort
from application.ports.outbound.email_service import EmailServicePort
from uuid import uuid4

from typing import Optional

@dataclass
class CreateAccountCommand:
    full_name: str
    email: str
    role: UserRole # only Teacher and admin allowed
    password: Optional[str] = None
    status: Optional[AccountStatus] = None
    
@dataclass
class CreateAccountResult:
    user: User
    temporary_password: Optional[str] = None
    
class CreateAccountUseCase:
    def __init__(self, user_repository: UserRepositoryPort, password_hasher: PasswordHasherPort, email_service: EmailServicePort):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.email_service = email_service
        
    def execute(self, command: CreateAccountCommand) -> CreateAccountResult:
        if self.user_repository.email_exists(command.email):
            raise EmailAlreadyExistsError(command.email)

        if command.password:
            raw_password = command.password
            must_change = False
        else:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            raw_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            must_change = True
        
        hashed = self.password_hasher.hash(raw_password)
        account_status = command.status or (AccountStatus.ACTIVE if command.password else AccountStatus.INACTIVE)
        
        new_user = User(
            id=uuid4(),
            email=command.email,
            full_name=command.full_name,
            role=command.role,
            status=account_status, 
            hashed_password=hashed,
            must_change_password=must_change
        )
        
        saved_user = self.user_repository.save(new_user)
        
        try:
            self.email_service.send_temporary_password_email(
                to_email=saved_user.email,
                full_name=saved_user.full_name,
                temporary_password=raw_password,
            )
        except Exception:
            pass
        
        return CreateAccountResult(user=saved_user, temporary_password=raw_password)