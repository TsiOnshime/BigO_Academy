"""
Implements PasswordHasherPort using django.contrib.auth.hashers.

These functions work independently of AUTH_USER_MODEL / Django's auth
app being wired up as the project's authentication system — they're pure
hashing utilities (PBKDF2 by default, configurable via PASSWORD_HASHERS
in settings), so using them here doesn't pull Django's auth machinery
into the domain/use-case layers. Only this adapter touches Django's
hasher API directly.
"""
from django.contrib.auth.hashers import check_password, make_password

from application.ports.outbound.password_hasher import PasswordHasherPort


class PasswordHasherAdapter(PasswordHasherPort):
    def hash(self, plain_password: str) -> str:
        return make_password(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return check_password(plain_password, hashed_password)