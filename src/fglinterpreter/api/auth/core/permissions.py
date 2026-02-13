"""Role-Based Access Control (RBAC) permission system.

This module defines permissions and their mappings to user roles.
Permissions control access to API endpoints and operations.
"""

from enum import Enum
from typing import Dict, Set


class Permission(str, Enum):
    """Permission enumeration for access control."""

    # Code execution permissions
    EXECUTE_CODE = "execute_code"
    COMPILE_CODE = "compile_code"
    PARSE_CODE = "parse_code"

    # File operations
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    DELETE_FILES = "delete_files"
    CREATE_FILES = "create_files"
    RENAME_FILES = "rename_files"

    # Database operations
    CONNECT_DATABASE = "connect_database"
    QUERY_DATABASE = "query_database"
    MODIFY_DATABASE = "modify_database"
    MANAGE_DB_CONFIGS = "manage_db_configs"

    # Terminal and remote access
    USE_TERMINAL = "use_terminal"
    USE_SFTP = "use_sftp"

    # Project management
    CREATE_PROJECT = "create_project"
    SAVE_PROJECT = "save_project"
    LOAD_PROJECT = "load_project"

    # Conversion operations
    CONVERT_CODE = "convert_code"
    CONFIGURE_CONVERSION = "configure_conversion"

    # User management (admin only)
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"

    # System management
    VIEW_LOGS = "view_logs"
    CONFIGURE_SYSTEM = "configure_system"
    VIEW_AUDIT_LOG = "view_audit_log"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    "admin": {
        # Code execution
        Permission.EXECUTE_CODE,
        Permission.COMPILE_CODE,
        Permission.PARSE_CODE,
        # File operations
        Permission.READ_FILES,
        Permission.WRITE_FILES,
        Permission.DELETE_FILES,
        Permission.CREATE_FILES,
        Permission.RENAME_FILES,
        # Database
        Permission.CONNECT_DATABASE,
        Permission.QUERY_DATABASE,
        Permission.MODIFY_DATABASE,
        Permission.MANAGE_DB_CONFIGS,
        # Terminal/Remote
        Permission.USE_TERMINAL,
        Permission.USE_SFTP,
        # Projects
        Permission.CREATE_PROJECT,
        Permission.SAVE_PROJECT,
        Permission.LOAD_PROJECT,
        # Conversion
        Permission.CONVERT_CODE,
        Permission.CONFIGURE_CONVERSION,
        # User management
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        # System
        Permission.VIEW_LOGS,
        Permission.CONFIGURE_SYSTEM,
        Permission.VIEW_AUDIT_LOG,
    },
    "developer": {
        # Code execution
        Permission.EXECUTE_CODE,
        Permission.COMPILE_CODE,
        Permission.PARSE_CODE,
        # File operations
        Permission.READ_FILES,
        Permission.WRITE_FILES,
        Permission.DELETE_FILES,
        Permission.CREATE_FILES,
        Permission.RENAME_FILES,
        # Database
        Permission.CONNECT_DATABASE,
        Permission.QUERY_DATABASE,
        Permission.MODIFY_DATABASE,
        Permission.MANAGE_DB_CONFIGS,
        # Terminal/Remote
        Permission.USE_TERMINAL,
        Permission.USE_SFTP,
        # Projects
        Permission.CREATE_PROJECT,
        Permission.SAVE_PROJECT,
        Permission.LOAD_PROJECT,
        # Conversion
        Permission.CONVERT_CODE,
        Permission.CONFIGURE_CONVERSION,
    },
    "viewer": {
        # Read-only access
        Permission.READ_FILES,
        Permission.PARSE_CODE,
        Permission.QUERY_DATABASE,  # Read-only queries
        Permission.LOAD_PROJECT,
        Permission.CONNECT_DATABASE,  # Can connect but not modify
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission.

    Args:
        role: User role (admin, developer, viewer)
        permission: Permission to check

    Returns:
        bool: True if role has permission, False otherwise
    """
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_role_permissions(role: str) -> Set[Permission]:
    """Get all permissions for a role.

    Args:
        role: User role

    Returns:
        Set[Permission]: Set of permissions for the role
    """
    return ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """Decorator to require a specific permission (for future use).

    Args:
        permission: Required permission

    Returns:
        Decorated function with permission requirement marker
    """

    def decorator(func):
        func.required_permission = permission
        return func

    return decorator
