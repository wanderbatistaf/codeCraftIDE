"""Authentication router for login, logout, token refresh, and user info.

This router provides the core authentication endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import auth_config
from ..core.rate_limiter import check_rate_limit
from ..core.security import create_access_token, create_refresh_token, decode_token
from ..database import AuthDatabase, get_auth_db
from ..dependencies.auth_deps import get_current_user
from ..models import (
    AuthStatusResponse,
    CurrentUser,
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from ..strategies import get_auth_strategy

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# HTTP Bearer security for token extraction
security = HTTPBearer(auto_error=False)


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """Get authentication status.

    Returns whether authentication is enabled and which strategy is active.
    This endpoint is public and doesn't require authentication.

    Returns:
        AuthStatusResponse: Authentication status information
    """
    return AuthStatusResponse(
        enabled=auth_config.enabled,
        strategy=auth_config.strategy if auth_config.enabled else None,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    db: AuthDatabase = Depends(get_auth_db),
):
    """Authenticate user and return tokens.

    This endpoint:
    1. Validates credentials against the configured auth strategy
    2. Checks rate limiting to prevent brute force attacks
    3. Creates access and refresh tokens
    4. Sets HTTPOnly cookies for token storage
    5. Logs the authentication event
    6. Updates user's last login timestamp

    Args:
        request: FastAPI request object
        response: FastAPI response object
        credentials: Login credentials (username and password)
        db: Auth database instance

    Returns:
        LoginResponse: Tokens and user information

    Raises:
        HTTPException: 400 if auth is disabled
        HTTPException: 429 if rate limit exceeded
        HTTPException: 401 if credentials are invalid
        HTTPException: 403 if account is inactive
    """
    if not auth_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled",
        )

    # Rate limiting
    client_ip = request.client.host
    if not check_rate_limit(db, credentials.username, client_ip):
        db.log_auth_event(
            username=credentials.username,
            event_type="failed_login",
            ip_address=client_ip,
            success=False,
            error_message="Rate limit exceeded",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    # Get authentication strategy
    strategy = get_auth_strategy()

    # Authenticate user
    user = await strategy.authenticate(credentials.username, credentials.password, db)

    if not user:
        # Log failed attempt
        db.record_login_attempt(credentials.username, client_ip, success=False)
        db.log_auth_event(
            username=credentials.username,
            event_type="failed_login",
            ip_address=client_ip,
            success=False,
            error_message="Invalid credentials",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Create session in database
    db.create_session(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent", ""),
    )

    # Update last login timestamp
    db.update_last_login(user.id)

    # Log successful login
    db.record_login_attempt(credentials.username, client_ip, success=True)
    db.log_auth_event(
        user_id=user.id,
        username=user.username,
        event_type="login",
        ip_address=client_ip,
        success=True,
    )

    # Set HTTPOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=auth_config.cookie_secure,
        samesite=auth_config.cookie_samesite,
        max_age=auth_config.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=auth_config.cookie_secure,
        samesite=auth_config.cookie_samesite,
        max_age=auth_config.refresh_token_expire_days * 24 * 60 * 60,
    )

    # Return tokens and user info
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            is_external=user.is_external,
            external_provider=user.external_provider,
            created_at=user.created_at,
            last_login=user.last_login,
        ),
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    db: AuthDatabase = Depends(get_auth_db),
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
):
    """Logout user and revoke tokens.

    This endpoint:
    1. Revokes the current session in the database
    2. Clears authentication cookies
    3. Logs the logout event

    Args:
        response: FastAPI response object
        current_user: Current authenticated user
        db: Auth database instance
        authorization: Authorization header with Bearer token (optional)
        access_token_cookie: Access token from cookie (optional)

    Returns:
        dict: Success message
    """
    # Get token from header or cookie
    token = None
    if authorization:
        token = authorization.credentials
    elif access_token_cookie:
        token = access_token_cookie

    if token:
        # Revoke session
        db.revoke_session(token)

        # Log logout
        db.log_auth_event(
            user_id=current_user.id,
            username=current_user.username,
            event_type="logout",
            success=True,
        )

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    response: Response,
    refresh_request: TokenRefreshRequest,
    db: AuthDatabase = Depends(get_auth_db),
):
    """Refresh access token using refresh token.

    This endpoint:
    1. Validates the refresh token
    2. Verifies the session is still active
    3. Creates a new access token
    4. Updates the session in the database
    5. Sets a new access token cookie

    Args:
        response: FastAPI response object
        refresh_request: Refresh token request
        db: Auth database instance

    Returns:
        TokenRefreshResponse: New access token

    Raises:
        HTTPException: 400 if auth is disabled
        HTTPException: 401 if refresh token is invalid or session expired
    """
    if not auth_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled",
        )

    # Decode refresh token
    payload = decode_token(refresh_request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify session
    if not db.is_refresh_token_valid(refresh_request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    # Get user
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )

    # Update session
    db.update_session_access_token(refresh_request.refresh_token, access_token)

    # Set new access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=auth_config.cookie_secure,
        samesite=auth_config.cookie_samesite,
        max_age=auth_config.access_token_expire_minutes * 60,
    )

    return TokenRefreshResponse(access_token=access_token)


@router.get("/me", response_model=CurrentUser)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Get current user information.

    This endpoint returns information about the currently authenticated user.
    Requires a valid access token.

    Args:
        current_user: Current authenticated user

    Returns:
        CurrentUser: Current user information
    """
    return current_user
