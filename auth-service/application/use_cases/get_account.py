from dataclasses import dataclass
from uuid import UUID

from domain.models import User
from domain.exceptions import UserNotFoundError
from application.ports.outbound.user_repository import UserRepositoryPort


@dataclass
class GetAccountCommand:
    user_id: UUID


class GetAccountUseCase:

    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    def execute(self, command: GetAccountCommand) -> User:

        user = self.user_repository.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(str(command.user_id))

        return user