from dataclasses import dataclass


from domain.exceptions import PasswordMismatchError, UserNotFoundError
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort
from application.ports.outbound.password_hasher import PasswordHasherPort


@dataclass
class ResetPasswordCommand:
    reset_token: str
    new_password: str
    confirm_password: str
    
class ResetPasswordUseCase:
    
    def __init__(self, user_repository: UserRepositoryPort,
                token_service: TokenServicePort, 
                password_hasher: PasswordHasherPort):
        self.user_repository = user_repository
        self.token_service = token_service
        self.password_hasher = password_hasher
        
    def execute(self, command: ResetPasswordCommand) -> None:
        if command.new_password != command.confirm_password:
            raise PasswordMismatchError()
        
        payload = self.token_service.validate_reset_token(command.reset_token)
        
        user = self.user_repository.find_by_id(payload.user_id)
        
        
        if user is None:
            raise UserNotFoundError(str(payload.user_id))
        
        user.hashed_password = self.password_hasher.hash(command.new_password)
        user.must_change_password = False
        self.user_repository.save(user)
        
        self.token_service.revoke_all_tokens_for_users(payload.user_id)
            
