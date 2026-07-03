from dataclasses import dataclass

from domain.models import User
from domain.exceptions import InvalidTokenError, AccountInactiveError
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort, TokenPair

@dataclass
class RefreshTokenCommand:
    refresh_token: str
    
@dataclass
class RefreshTokenResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: User
    
class RefreshTokenUseCase:
    def __init__(self, user_repository: UserRepositoryPort, token_service: TokenServicePort):
        self.user_repository = user_repository
        self.token_service = token_service
    
    def execute(self, command: RefreshTokenCommand) -> RefreshTokenResult:
        payload = self.token_service.validate_refresh_token(command.refresh_token)
        
        
        user = self.user_repository.find_by_id(payload.user_id)
        
        if user is None:
            raise InvalidTokenError("User no longer exists")
        
        if not user.is_active():
            raise AccountInactiveError()
        
        self.token_service.revoke_refresh_token(command.refresh_token)
        
        token_pair: TokenPair = self.token_service.generate_tokens(user)
        
        
        return RefreshTokenResult(
            access_token= token_pair.access_token,
            refresh_token = token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            user=User
            
            
        )
        