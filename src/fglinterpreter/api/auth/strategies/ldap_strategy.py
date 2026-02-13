"""LDAP authentication strategy.

This strategy authenticates users against an LDAP/Active Directory server.
"""

from typing import Optional

from ..config import auth_config
from ..database import AuthDatabase, AuthUser
from .base import AuthStrategy


class LDAPAuthStrategy(AuthStrategy):
    """LDAP/Active Directory authentication strategy."""

    async def authenticate(
        self, username: str, password: str, db: AuthDatabase
    ) -> Optional[AuthUser]:
        """Authenticate user with LDAP server.

        Args:
            username: Username
            password: Plain text password
            db: Auth database instance

        Returns:
            Optional[AuthUser]: User if authenticated, None otherwise
        """
        # TODO: Implement LDAP authentication
        # This is a stub implementation for Phase 5

        # Check if LDAP is configured
        if not auth_config.ldap_server or not auth_config.ldap_base_dn:
            return None

        # Future implementation will:
        # 1. Connect to LDAP server
        # 2. Bind with provided credentials
        # 3. Search for user in directory
        # 4. Verify user attributes
        # 5. Create/update user in local database if authenticated
        # 6. Return user object

        return None

    def get_strategy_name(self) -> str:
        """Get strategy name.

        Returns:
            str: Strategy name
        """
        return "ldap"
