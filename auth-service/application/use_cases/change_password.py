from dataclasses import dataclass

from domain.exceptions import IncorrectPasswordError, PasswordMismatchError, UserNotFoundError

from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.password_hasher import PasswordHasherPort
from application.ports.outbound.token_service import TokenServicePort

from uuid import UUID


@dataclass
class ChangePasswordCommand:
    user_id: UUID
    current_password: str
    new_password: str
    confirm_password: str
    
    
class ChangePasswordUseCase:
    def __init__(self, user_repository: UserRepositoryPort, password_hasher: PasswordHasherPort, token_service: TokenServicePort):
        self.user_repository = user_repository
        self.token_service = token_service
        self.password_hasher = password_hasher
    def execute (self, command: ChangePasswordCommand) -> None:
        user = self.user_repository.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(str(command.user_id))

        if user.hashed_password is None:
            raise IncorrectPasswordError()
        
        password_valid = self.password_hasher.verify(command.current_password, user.hashed_password)
        
        if not password_valid:
            raise IncorrectPasswordError()
        
        if command.new_password != command.confirm_password:
            raise PasswordMismatchError()
        user.hashed_password = self.password_hasher.hash(command.new_password)
        user.must_change_password = False
        self.user_repository.save(user)
        
        
        self.token_service.revoke_all_tokens_for_users(command.user_id)
        
    