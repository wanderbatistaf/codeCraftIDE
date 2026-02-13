"""Pydantic models for authentication API.

These models define the request and response schemas for authentication
endpoints and internal data structures.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# Role constants
class UserRole:
    """User role constants."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


# Base user model
class UserBase(BaseModel):
    """Base user model with common fields."""

    username: str = Field(..., min_length=3, max_length=255, description="Username")
    email: EmailStr = Field(..., description="Email address")
    role: Literal["admin", "developer", "viewer"] = Field(default="viewer", description="User role")


# User creation request
class UserCreate(UserBase):
    """Model for creating a new user."""

    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


# User update request
class UserUpdate(BaseModel):
    """Model for updating a user."""

    email: Optional[EmailStr] = Field(default=None, description="Email address")
    role: Optional[Literal["admin", "developer", "viewer"]] = Field(
        default=None, description="User role"
    )
    is_active: Optional[bool] = Field(default=None, description="Active status")
    password: Optional[str] = Field(default=None, min_length=8, description="New password")


# User response (what API returns)
class UserResponse(UserBase):
    """Model for user response (excludes sensitive data)."""

    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user is active")
    is_external: bool = Field(..., description="Whether user is from external auth")
    external_provider: Optional[str] = Field(
        default=None, description="External auth provider (ldap, keycloak)"
    )
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# Login request
class LoginRequest(BaseModel):
    """Login request with credentials."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


# Login response
class LoginResponse(BaseModel):
    """Login response with tokens and user info."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


# Token refresh request
class TokenRefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


# Token refresh response
class TokenRefreshResponse(BaseModel):
    """Token refresh response."""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


# Current user model (used in dependencies)
class CurrentUser(BaseModel):
    """Current authenticated user model."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    is_external: bool = Field(default=False, description="Whether user is from external auth")
    external_provider: Optional[str] = Field(default=None, description="External auth provider")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    def is_developer(self) -> bool:
        """Check if user is developer or admin."""
        return self.role in [UserRole.ADMIN, UserRole.DEVELOPER]

    def is_viewer(self) -> bool:
        """Check if user is viewer (or any role)."""
        return self.role in [UserRole.ADMIN, UserRole.DEVELOPER, UserRole.VIEWER]


# Auth status response (for health check)
class AuthStatusResponse(BaseModel):
    """Authentication status response."""

    enabled: bool = Field(..., description="Whether auth is enabled")
    strategy: Optional[str] = Field(default=None, description="Auth strategy (jwt, ldap, keycloak)")
