"""Base authentication strategy interface.

This module defines the abstract base class for authentication strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..database import AuthDatabase, AuthUser


class AuthStrategy(ABC):
    """Abstract base class for authentication strategies."""

    @abstractmethod
    async def authenticate(
        self, username: str, password: str, db: AuthDatabase
    ) -> Optional[AuthUser]:
        """Authenticate a user with username and password.

        Args:
            username: Username
            password: Password
            db: Auth database instance

        Returns:
            Optional[AuthUser]: Authenticated user if successful, None otherwise
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the strategy name.

        Returns:
            str: Strategy name
        """
        pass
