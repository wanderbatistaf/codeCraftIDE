"""Rate limiting for login attempts.

This module provides rate limiting functionality to prevent brute force attacks
on the authentication system.
"""

from ..config import auth_config
from ..database import AuthDatabase


def check_rate_limit(db: AuthDatabase, username: str, ip_address: str) -> bool:
    """Check if a login attempt is within rate limits.

    Args:
        db: Auth database instance
        username: Username attempting to login
        ip_address: Client IP address

    Returns:
        bool: True if within limits, False if rate limited
    """
    failed_attempts = db.get_failed_login_attempts(
        username=username,
        ip_address=ip_address,
        minutes=auth_config.login_attempt_window_minutes,
    )

    return failed_attempts < auth_config.max_login_attempts


def record_login_attempt(db: AuthDatabase, username: str, ip_address: str, success: bool) -> None:
    """Record a login attempt for rate limiting.

    Args:
        db: Auth database instance
        username: Username
        ip_address: Client IP address
        success: Whether the login was successful
    """
    db.record_login_attempt(username, ip_address, success)
