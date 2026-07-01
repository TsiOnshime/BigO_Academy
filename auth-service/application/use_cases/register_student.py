from dataclasses import dataclass
from uuid import uuid4

from domain.models import User
from domain.enums import UserRole, AccountStatus
from domain.exceptions import PasswordMismatchError, EmailAlreadyExistsError
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort, TokenPair
from application.ports.outbound.password_hasher import PasswordHasherPort


@dataclass
class RegisterStudentCommand:
    """
    The input data this use case needs.
    Mirrors the RegisterRequest schema from the API spec.
    Named 'Command' because it represents an instruction to do something.
    """
    full_name: str
    email: str
    password: str
    confirm_password: str


@dataclass
class RegisterStudentResult:
    """
    The output this use case returns.
    Mirrors the AuthResponse schema from the API spec.
    """
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: User


class RegisterStudentUseCase:

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        token_service: TokenServicePort,
        password_hasher: PasswordHasherPort,
    ):
        self.user_repository = user_repository
        self.token_service = token_service
        self.password_hasher = password_hasher

    def execute(self, command: RegisterStudentCommand) -> RegisterStudentResult:

        # Step 1 — passwords must match
        if command.password != command.confirm_password:
            raise PasswordMismatchError()
        # Step 2 — email must not already be registered
        if self.user_repository.email_exists(command.email):
            raise EmailAlreadyExistsError(command.email)
        
        hashed = self.password_hasher.hash(command.password)
        
        new_user = User(
            id=uuid4(),
            email=command.email,
            full_name=command.full_name,
            role=UserRole.STUDENT, 
            status=AccountStatus.ACTIVE, 
            hashed_password=hashed, 
            must_change_password=False,
        )
        
        saved_user = self.user_repository.save(new_user)
        
        token_pair : TokenPair = self.token_service.generate_tokens(saved_user)
        
        return RegisterStudentResult(
            access_token=token_pair.access_token, 
            refresh_token=token_pair.refresh_token, 
            token_type=token_pair.token_type,
            expires_is=token_pair.expires_in,
            user=saved_user,
        )