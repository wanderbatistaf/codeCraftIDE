"""JWT authentication strategy.

This strategy authenticates users against the local database
using username and hashed password.
"""

from typing import Optional

from ..core.security import verify_password
from ..database import AuthDatabase, AuthUser
from .base import AuthStrategy


class JWTAuthStrategy(AuthStrategy):
    """JWT authentication strategy using local database."""

    async def authenticate(
        self, username: str, password: str, db: AuthDatabase
    ) -> Optional[AuthUser]:
        """Authenticate user with local database.

        Args:
            username: Username
            password: Plain text password
            db: Auth database instance

        Returns:
            Optional[AuthUser]: User if authenticated, None otherwise
        """
        # Get user from database
        user = db.get_user_by_username(username)

        if not user:
            return None

        # Check if user is external (shouldn't use JWT for external users)
        if user.is_external:
            return None

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            return None

        return user

    def get_strategy_name(self) -> str:
        """Get strategy name.

        Returns:
            str: Strategy name
        """
        return "jwt"
