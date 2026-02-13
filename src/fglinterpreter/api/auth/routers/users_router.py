"""User management router (admin only).

This router provides endpoints for managing users in the system.
All endpoints require admin role.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.security import hash_password, validate_password_strength
from ..database import AuthDatabase, get_auth_db
from ..dependencies.auth_deps import require_role
from ..models import CurrentUser, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["user-management"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AuthDatabase = Depends(get_auth_db),
    include_inactive: bool = False,
):
    """List all users (admin only).

    Args:
        current_user: Current authenticated admin user
        db: Auth database instance
        include_inactive: Include inactive users in the list

    Returns:
        List[UserResponse]: List of users
    """
    users = db.list_users(include_inactive=include_inactive)

    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            is_external=user.is_external,
            external_provider=user.external_provider,
            created_at=user.created_at,
            last_login=user.last_login,
        )
        for user in users
    ]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AuthDatabase = Depends(get_auth_db),
):
    """Create a new user (admin only).

    Args:
        user_data: User creation data
        current_user: Current authenticated admin user
        db: Auth database instance

    Returns:
        UserResponse: Created user

    Raises:
        HTTPException: 400 if username or email already exists
        HTTPException: 400 if password is too weak
    """
    # Check if username already exists
    existing_user = db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if email already exists
    existing_email = db.get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create user
    user_id = db.create_user(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        is_external=False,
        external_provider=None,
    )

    # Get created user
    user = db.get_user_by_id(user_id)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        is_external=user.is_external,
        external_provider=user.external_provider,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AuthDatabase = Depends(get_auth_db),
):
    """Get user by ID (admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Auth database instance

    Returns:
        UserResponse: User information

    Raises:
        HTTPException: 404 if user not found
    """
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        is_external=user.is_external,
        external_provider=user.external_provider,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AuthDatabase = Depends(get_auth_db),
):
    """Update user information (admin only).

    Args:
        user_id: User ID
        user_data: User update data
        current_user: Current authenticated admin user
        db: Auth database instance

    Returns:
        UserResponse: Updated user

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if email already exists
        HTTPException: 400 if password is too weak
    """
    # Check if user exists
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if email already exists (if updating email)
    if user_data.email and user_data.email != user.email:
        existing_email = db.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

    # Validate password strength (if updating password)
    password_hash = None
    if user_data.password:
        is_valid, error_message = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        password_hash = hash_password(user_data.password)

    # Update user
    db.update_user(
        user_id=user_id,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        is_active=user_data.is_active,
    )

    # Get updated user
    user = db.get_user_by_id(user_id)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        is_external=user.is_external,
        external_provider=user.external_provider,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: AuthDatabase = Depends(get_auth_db),
):
    """Delete user (admin only).

    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Auth database instance

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if trying to delete yourself
    """
    # Check if user exists
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Delete user
    db.delete_user(user_id)

    # Return 204 No Content (no body)
    return None
