"""FastAPI dependencies for authentication."""

from .auth_deps import (
    get_current_user,
    get_current_user_optional,
    require_permission,
    require_role,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_permission",
    "require_role",
]
