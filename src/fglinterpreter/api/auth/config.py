"""Authentication configuration.

This module loads authentication configuration from environment variables
and provides a centralized configuration object for the auth system.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration."""

    # Enable/disable authentication
    enabled: bool = Field(default=False, description="Enable authentication system")
    strategy: str = Field(
        default="jwt", description="Authentication strategy (jwt, ldap, keycloak)"
    )

    # JWT settings
    jwt_secret_key: str = Field(
        default="dev-secret-change-in-production-INSECURE",
        description="JWT secret key for token signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Database settings
    db_type: str = Field(default="sqlite", description="Database type (sqlite, postgres, mysql)")
    db_path: Optional[str] = Field(default=None, description="Database path (for SQLite)")
    use_main_db: bool = Field(default=False, description="Use main application database for auth")

    # LDAP settings (if strategy=ldap)
    ldap_server: Optional[str] = Field(default=None, description="LDAP server URL")
    ldap_base_dn: Optional[str] = Field(default=None, description="LDAP base DN")
    ldap_user_dn_template: Optional[str] = Field(default=None, description="LDAP user DN template")
    ldap_bind_dn: Optional[str] = Field(
        default=None, description="LDAP bind DN for admin operations"
    )
    ldap_bind_password: Optional[str] = Field(default=None, description="LDAP bind password")

    # Keycloak settings (if strategy=keycloak)
    keycloak_server_url: Optional[str] = Field(default=None, description="Keycloak server URL")
    keycloak_realm: Optional[str] = Field(default=None, description="Keycloak realm")
    keycloak_client_id: Optional[str] = Field(default=None, description="Keycloak client ID")
    keycloak_client_secret: Optional[str] = Field(
        default=None, description="Keycloak client secret"
    )

    # Security settings
    password_min_length: int = Field(default=8, description="Minimum password length")
    max_login_attempts: int = Field(
        default=5, description="Maximum failed login attempts before lockout"
    )
    login_attempt_window_minutes: int = Field(
        default=15, description="Time window for login attempt tracking (minutes)"
    )
    cookie_secure: bool = Field(default=False, description="Use secure cookies (HTTPS only)")
    cookie_samesite: str = Field(
        default="lax", description="Cookie SameSite attribute (lax, strict, none)"
    )

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


def load_auth_config() -> AuthConfig:
    """Load authentication configuration from environment variables.

    Returns:
        AuthConfig: Configuration object with values from environment
    """
    # Get default auth database path
    default_auth_db_path = str(Path.home() / ".fglinterpreter" / "auth.db")

    return AuthConfig(
        # Core settings
        enabled=os.getenv("AUTH_ENABLED", "false").lower() == "true",
        strategy=os.getenv("AUTH_STRATEGY", "jwt"),
        # JWT
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production-INSECURE"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        # Database
        db_type=os.getenv("AUTH_DB_TYPE", "sqlite"),
        db_path=os.getenv("AUTH_DB_PATH", default_auth_db_path),
        use_main_db=os.getenv("AUTH_USE_MAIN_DB", "false").lower() == "true",
        # LDAP
        ldap_server=os.getenv("LDAP_SERVER"),
        ldap_base_dn=os.getenv("LDAP_BASE_DN"),
        ldap_user_dn_template=os.getenv("LDAP_USER_DN_TEMPLATE"),
        ldap_bind_dn=os.getenv("LDAP_BIND_DN"),
        ldap_bind_password=os.getenv("LDAP_BIND_PASSWORD"),
        # Keycloak
        keycloak_server_url=os.getenv("KEYCLOAK_SERVER_URL"),
        keycloak_realm=os.getenv("KEYCLOAK_REALM"),
        keycloak_client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
        keycloak_client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET"),
        # Security
        password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
        max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
        login_attempt_window_minutes=int(os.getenv("LOGIN_ATTEMPT_WINDOW_MINUTES", "15")),
        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        cookie_samesite=os.getenv("COOKIE_SAMESITE", "lax"),
    )


# Global configuration instance
auth_config = load_auth_config()
