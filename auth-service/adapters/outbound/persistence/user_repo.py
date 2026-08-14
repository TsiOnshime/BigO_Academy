from uuid import UUID

from application.ports.outbound.user_repository import UserRepositoryPort
from core.models import DjangoUser
from domain.enums import AccountStatus, OAuthProvider, UserRole
from domain.models import User


class UserRepository(UserRepositoryPort):
    """Django ORM implementation of UserRepositoryPort."""

    def _map_to_domain(self, orm_user: DjangoUser) -> User:
        return User(
            id=orm_user.id,
            email=orm_user.email,
            full_name=orm_user.full_name,
            role=UserRole(orm_user.role),
            status=AccountStatus(orm_user.status),
            hashed_password=orm_user.hashed_password,
            oauth_providers=[
                OAuthProvider(provider)
                for provider in orm_user.oauth_providers
            ],
            must_change_password=orm_user.must_change_password,
            created_at=orm_user.created_at,
            updated_at=orm_user.updated_at,
        )

    def _map_to_orm(self, user: User) -> DjangoUser:
        try:
            orm_user = DjangoUser.objects.get(id=user.id)
        except DjangoUser.DoesNotExist:
            orm_user = DjangoUser(id=user.id)

        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        status_val = user.status.value if hasattr(user.status, "value") else str(user.status)

        orm_user.email = user.email
        orm_user.full_name = user.full_name
        orm_user.role = role_val
        orm_user.status = status_val
        orm_user.hashed_password = user.hashed_password
        orm_user.oauth_providers = [
            provider.value if hasattr(provider, "value") else str(provider)
            for provider in user.oauth_providers
        ]
        orm_user.must_change_password = user.must_change_password

        return orm_user

    def save(self, user: User) -> User:
        orm_user = self._map_to_orm(user)
        orm_user.save()
        return self._map_to_domain(orm_user)

    def find_by_email(self, email: str) -> User | None:
        try:
            orm_user = DjangoUser.objects.get(email=email)
            return self._map_to_domain(orm_user)
        except DjangoUser.DoesNotExist:
            return None

    def find_by_id(self, user_id: UUID) -> User | None:
        try:
            orm_user = DjangoUser.objects.get(id=user_id)
            return self._map_to_domain(orm_user)
        except DjangoUser.DoesNotExist:
            return None

    def email_exists(self, email: str) -> bool:
        return DjangoUser.objects.filter(email=email).exists()