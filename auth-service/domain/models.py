from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


from domain.enums import UserRole, AccountStatus, OAuthProvider

@dataclass
class User:
    id: UUID
    email: str
    full_name: str
    role: UserRole
    status: AccountStatus
    hashed_password: str | None
    oauth_providers: list[OAuthProvider] = field(default_factory=list)
    must_change_password: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE
    def has_oauth_provider(self, provider: OAuthProvider) -> bool:
        return provider in self.oauth_providers
    