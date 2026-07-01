from dataclasses import dataclass
from domain.exceptions import InvalidCredentialsError, AccountInactiveError
from domain.models import User
from application.ports.outbound.password_hasher import PasswordHasherPort
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort, TokenPair


@dataclass
class LoginCommand:
    email: str
    password: str

@dataclass
class LoginResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: User
    
class LoginUseCase:
    def __init__(self, user_repository: UserRepositoryPort, token_service: TokenServicePort, 
    password_hasher: PasswordHasherPort):
        self.user_repository = user_repository
        self.token_service = token_service
        self.password_hasher = password_hasher
    def execute(self, command: LoginCommand) -> LoginResult:
        user = self.user_repository.find_by_email(command.email)
        if not user:
            raise InvalidCredentialsError()
        if not user.is_active():
            raise AccountInactiveError()
        password_valid = self.password_hasher.verify(command.password, user.hashed_password)
        
        if not password_valid:
            raise InvalidCredentialsError()
        token_pair : TokenPair = self.token_service.generate_tokens(user)
        
        return LoginResult(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type, 
            expires_in=token_pair.expires_in,
            user=user,
        ) 
        