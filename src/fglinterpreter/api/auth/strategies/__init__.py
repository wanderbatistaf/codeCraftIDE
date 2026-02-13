"""Authentication strategies."""

from .base import AuthStrategy
from .jwt_strategy import JWTAuthStrategy

__all__ = ["AuthStrategy", "JWTAuthStrategy"]


def get_auth_strategy() -> AuthStrategy:
    """Get the configured authentication strategy.

    Returns:
        AuthStrategy: Authentication strategy instance
    """
    from ..config import auth_config

    if auth_config.strategy == "jwt":
        return JWTAuthStrategy()
    elif auth_config.strategy == "ldap":
        from .ldap_strategy import LDAPAuthStrategy

        return LDAPAuthStrategy()
    elif auth_config.strategy == "keycloak":
        from .keycloak_strategy import KeycloakAuthStrategy

        return KeycloakAuthStrategy()
    else:
        # Default to JWT
        return JWTAuthStrategy()
