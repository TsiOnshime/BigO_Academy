from dataclasses import dataclass

from uuid import UUID
from domain.exceptions import UserNotFoundError
from domain.enums import AccountStatus
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort

@dataclass
class DeactivateAccountCommand:
    user_id: UUID
    
    
class DeactivateAccountUseCase:
    def __init__(self, user_repository: UserRepositoryPort, token_service: TokenServicePort):
        self.user_repository = user_repository
        self.token_service = token_service
        
    def execute(self, command: DeactivateAccountCommand):
        user = self.user_repository.find_by_id(command.user_id)
        
        if user is None:
            raise UserNotFoundError(str(command.user_id))
        
        user.status = AccountStatus.INACTIVE
        saved_user = self.user_repository.save(user)
        
        self.token_service.revoke_all_tokens_for_users(command.user_id)
        
        return saved_user
        
        
        
        
        