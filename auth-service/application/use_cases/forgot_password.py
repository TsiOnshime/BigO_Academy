from dataclasses import dataclass

from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.otp_service import OtpServicePort
from application.ports.outbound.email_service import EmailServicePort




@dataclass
class ForgotPasswordCommand:
    email: str
    
class ForgotPasswordUseCase:
    def __init__(self, user_repository: UserRepositoryPort, otp_service: OtpServicePort, email_service: EmailServicePort):
        self.user_repository = user_repository
        self.otp_service = otp_service
        self.email_service = email_service
        
    def execute(self, command: ForgotPasswordCommand) -> None:
        user = self.user_repository.find_by_email(command.email)
        
        if user is None:
            return 
        
        otp = self.otp_service.generate_and_store_otp(command.email)
        
        self.email_service.send_otp_email(command.email, otp)