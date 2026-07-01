from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    """
    Abstract contract for hashing and verifying passwords.
    Implemented using Django's password hashers in the adapter layer.
    Keeps Django's auth module out of the use cases.
    """

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Hash a plain text password. Returns the hashed string."""
        

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Check if a plain text password matches a stored hash.
        Returns True if they match, False otherwise.
        """
        