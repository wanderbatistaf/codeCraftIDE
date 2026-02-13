"""FastAPI authentication dependencies.

These dependencies are used to protect endpoints and verify user permissions.
"""

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import auth_config
from ..core.permissions import Permission, has_permission
from ..core.security import decode_token
from ..database import AuthDatabase, get_auth_db
from ..models import CurrentUser

# HTTP Bearer security scheme (for Authorization header)
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None),
    db: AuthDatabase = Depends(get_auth_db),
) -> Optional[CurrentUser]:
    """Get current user from token (optional).

    Returns None if:
    - Auth is disabled
    - No token provided
    - Token is invalid
    - User not found or inactive

    Args:
        authorization: Authorization header with Bearer token (optional)
        access_token: Access token from cookie (optional)
        db: Auth database instance

    Returns:
        Optional[CurrentUser]: Current user if authenticated, None otherwise
    """
    # If auth is disabled, return None (all access allowed)
    if not auth_config.enabled:
        return None

    # Try to get token from Authorization header or cookie
    token = None
    if authorization:
        token = authorization.credentials
    elif access_token:
        token = access_token

    if not token:
        return None

    # Decode token
    payload = decode_token(token)
    if not payload:
        return None

    # Verify token type
    if payload.get("type") != "access":
        return None

    # Get user ID from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = int(user_id_str)
    except ValueError:
        return None

    # Verify session is still valid
    if not db.is_session_valid(token):
        return None

    # Get user from database
    user = db.get_user_by_id(user_id)
    if not user or not user.is_active:
        return None

    # Update last activity
    db.update_session_activity(token)

    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


async def get_current_user(
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
) -> CurrentUser:
    """Get current user (required).

    If auth is disabled, returns a default admin user.
    If auth is enabled but user is not authenticated, raises 401.

    Args:
        current_user: Current user from get_current_user_optional

    Returns:
        CurrentUser: Current authenticated user

    Raises:
        HTTPException: 401 if not authenticated and auth is enabled
    """
    # If auth is disabled, return a default admin user
    if not auth_config.enabled:
        return CurrentUser(
            id=0,
            username="default",
            email="default@localhost",
            role="admin",
            is_active=True,
        )

    # If auth is enabled, user must be authenticated
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


def require_role(*roles: str):
    """Dependency factory to require specific roles.

    Args:
        *roles: Required roles (e.g., "admin", "developer")

    Returns:
        Dependency function that checks user role

    Raises:
        HTTPException: 403 if user doesn't have required role
    """

    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        """Check if user has required role.

        Args:
            current_user: Current authenticated user

        Returns:
            CurrentUser: Current user if authorized

        Raises:
            HTTPException: 403 if user doesn't have required role
        """
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(roles)}",
            )
        return current_user

    return role_checker


def require_permission(permission: Permission):
    """Dependency factory to require specific permission.

    Args:
        permission: Required permission

    Returns:
        Dependency function that checks user permission

    Raises:
        HTTPException: 403 if user doesn't have required permission
    """

    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        """Check if user has required permission.

        Args:
            current_user: Current authenticated user

        Returns:
            CurrentUser: Current user if authorized

        Raises:
            HTTPException: 403 if user doesn't have required permission
        """
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required permission: {permission.value}",
            )
        return current_user

    return permission_checker
