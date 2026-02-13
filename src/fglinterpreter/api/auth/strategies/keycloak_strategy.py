"""Keycloak/OAuth2 authentication strategy.

This strategy authenticates users using Keycloak or other OAuth2 providers.
"""

from typing import Optional

from ..config import auth_config
from ..database import AuthDatabase, AuthUser
from .base import AuthStrategy


class KeycloakAuthStrategy(AuthStrategy):
    """Keycloak/OAuth2 authentication strategy."""

    async def authenticate(
        self, username: str, password: str, db: AuthDatabase
    ) -> Optional[AuthUser]:
        """Authenticate user with Keycloak.

        Args:
            username: Username
            password: Plain text password
            db: Auth database instance

        Returns:
            Optional[AuthUser]: User if authenticated, None otherwise
        """
        # TODO: Implement Keycloak authentication
        # This is a stub implementation for Phase 5

        # Check if Keycloak is configured
        if (
            not auth_config.keycloak_server_url
            or not auth_config.keycloak_realm
            or not auth_config.keycloak_client_id
        ):
            return None

        # Future implementation will:
        # 1. Exchange credentials for Keycloak token
        # 2. Validate token with Keycloak server
        # 3. Extract user info from token
        # 4. Create/update user in local database if authenticated
        # 5. Return user object

        return None

    def get_strategy_name(self) -> str:
        """Get strategy name.

        Returns:
            str: Strategy name
        """
        return "keycloak"
