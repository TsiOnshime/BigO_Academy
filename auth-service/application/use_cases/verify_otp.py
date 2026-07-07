from dataclasses import dataclass


from domain.exceptions import InvalidOtpError, UserNotFoundError
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.otp_service import OtpServicePort
from application.ports.outbound.token_service import TokenServicePort



@dataclass
class VerifyOtpCommand:
    email: str
    otp: str
    
@dataclass
class VerifyOtpResult:
    reset_token: str
    expires_in: int # always 300 seconds
    
    
class VerifyOtpUseCase:
    def __init__(self, user_repository: UserRepositoryPort, otp_service: OtpServicePort, token_service: TokenServicePort):
        self.user_repository = user_repository
        self.otp_service = otp_service
        self.token_service = token_service
        
        
    def execute(self, command: VerifyOtpCommand) -> VerifyOtpResult:
        user = self.user_repository.find_by_email(command.email)
        if user is None:
            raise InvalidOtpError()
        
        is_valid = self.otp_service.verify_otp(command.email, command.otp)
        
        if not is_valid:
            raise InvalidOtpError()
        
        reset_token = self.token_service.generate_reset_token(user)
        
        return VerifyOtpResult(
            reset_token=reset_token,
            expires_in=300,
        )
            
    