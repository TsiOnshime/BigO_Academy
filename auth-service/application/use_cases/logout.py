from dataclasses import dataclass

from application.ports.outbound.token_service import TokenServicePort

@dataclass
class LogoutCommand:
    refresh_token: str
    
class LogoutUseCase:
    def __init__(self, token_service: TokenServicePort):
        self.token_service = token_service
        
    def execute(self, command: LogoutCommand) -> None:
        self.token_service.validate_refresh_token(command.refresh_token)
        self.token_service.revoke_refresh_token(command.refresh_token)