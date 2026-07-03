from dataclasses import dataclass
from uuid import UUID

from domain.models import User
from domain.exceptions import UserNotFoundError, AccountInactiveError
from application.ports.outbound.user_repository import UserRepositoryPort


@dataclass
class GetCurrentUserCommand:
    user_id: UUID


class GetCurrentUserUseCase:

    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    def execute(self, command: GetCurrentUserCommand) -> User:

        user = self.user_repository.find_by_id(command.user_id)

        if user is None:
            raise UserNotFoundError(str(command.user_id))

        if not user.is_active():
            raise AccountInactiveError()

        return user