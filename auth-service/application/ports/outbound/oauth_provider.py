from abc import ABC, abstractmethod

from dataclasses import dataclass


@dataclass
class OAuthUserProfile:
    """
    The user profile data we get back from Google or GitHub.
    Both providers give us at minimum: email and full name.
    """
    email: str
    full_name: str
    provider: str
    provider_user_id: str
    
class OAuthProviderPort(ABC):
    """
    Abstract contract for exchanging an OAuth authorization code
    for a user profile. Implemented separately for Google and GitHub.
    """
    
    @abstractmethod
    def get_user_profile(self, authorization_code: str) -> OAuthUserProfile:
        """
        Exchange the authorization code for tokens,
        then fetch and return the user's profile.
        Raises InvalidTokenError if the code is invalid or expired.
        """
        
    