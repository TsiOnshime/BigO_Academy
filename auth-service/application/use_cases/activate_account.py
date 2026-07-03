from dataclasses import dataclass
from uuid import UUID

from domain.models import User
from domain.enums import AccountStatus
from domain.exceptions import UserNotFoundError
from application.ports.outbound.user_repository import UserRepositoryPort


@dataclass
class ActivateAccountCommand:
    user_id: UUID


class ActivateAccountUseCase:

    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    def execute(self, command: ActivateAccountCommand) -> User:

        user = self.user_repository.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(str(command.user_id))

        # Set status to ACTIVE regardless of current status
        # Idempotent — activating an already active account is harmless
        user.status = AccountStatus.ACTIVE
        return self.user_repository.save(user)