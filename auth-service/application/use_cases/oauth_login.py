from dataclasses import dataclass

from domain.models import User
from domain.enums import UserRole, AccountStatus, OAuthProvider
from domain.exceptions import AccountInactiveError

from application.ports.outbound.user_repository import UserRepositoryPort
from application.ports.outbound.token_service import TokenServicePort
from application.ports.outbound.oauth_provider import OAuthProviderPort, OAuthUserProfile
from uuid import uuid4

@dataclass
class OAuthLoginCommand:
    authorization_code:str
    provider: OAuthProvider
    
    
@dataclass
class OAuthLoginResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: User
    is_new_user: bool


class OAuthLoginUseCase:
    def __init__(self, user_repository: UserRepositoryPort, token_service: TokenServicePort, oauth_provider: OAuthProviderPort):
        self.user_repository = user_repository
        self.token_service = token_service
        self.oauth_provider = oauth_provider
    
    def execute(self, command: OAuthLoginCommand) -> OAuthLoginResult:
        profile: OAuthUserProfile = self.oauth_provider.get_user_profile(command.authorization_code)

        existing_user = self.user_repository.find_by_email(profile.email)
        is_new_user = existing_user is None
        
        if existing_user is not None:
            if not existing_user.is_active():
                raise AccountInactiveError()
            if not existing_user.has_oauth_provider(command.provider):
                existing_user.oauth_providers.append(command.provider)
                self.user_repository.save(existing_user)
            user = existing_user
        else:
            user = User(
                id=uuid4(),
                email=profile.email,
                full_name=profile.full_name,
                role=UserRole.STUDENT,
                status=AccountStatus.ACTIVE,
                hashed_password=None,
                oauth_providers=[command.provider],
                must_change_password=False,
            )
            user = self.user_repository.save(user)
        token_pair = self.token_service.generate_tokens(user)
        
        return OAuthLoginResult(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            user=user,
            is_new_user=is_new_user
        )           
                