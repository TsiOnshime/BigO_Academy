from dataclasses import dataclass
from uuid import UUID
import secrets
import string

from domain.models import User
from domain.exceptions import UserNotFoundError
from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort
from application.ports.outbound.password_hasher import PasswordHasherPort
from application.ports.outbound.email_service import EmailServicePort


@dataclass
class AdminResetPasswordCommand:
    user_id: UUID


class AdminResetPasswordUseCase:

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        token_service: TokenServicePort,
        password_hasher: PasswordHasherPort,
        email_service: EmailServicePort,
    ):
        self.user_repository = user_repository
        self.token_service = token_service
        self.password_hasher = password_hasher
        self.email_service = email_service

    def execute(self, command: AdminResetPasswordCommand) -> None:


        user = self.user_repository.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(str(command.user_id))


        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        temporary_password = ''.join(
            secrets.choice(alphabet) for _ in range(12)
        )

        user.hashed_password = self.password_hasher.hash(temporary_password)
        user.must_change_password = True
        self.user_repository.save(user)

        
        self.token_service.revoke_all_tokens_for_user(command.user_id)

    
        self.email_service.send_temporary_password_email(
            to_email=user.email,
            full_name=user.full_name,
            temporary_password=temporary_password,
        )