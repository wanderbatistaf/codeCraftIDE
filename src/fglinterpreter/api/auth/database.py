"""Authentication database management.

This module handles the authentication database schema, initialization,
and all CRUD operations for users, sessions, audit logs, and rate limiting.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .config import auth_config


class AuthUser:
    """User data class."""

    def __init__(
        self,
        id: int,
        username: str,
        email: str,
        password_hash: Optional[str],
        role: str,
        is_active: bool,
        is_external: bool,
        external_provider: Optional[str],
        created_at: datetime,
        last_login: Optional[datetime],
        metadata: Optional[Dict],
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.is_external = is_external
        self.external_provider = external_provider
        self.created_at = created_at
        self.last_login = last_login
        self.metadata = metadata or {}


class AuthDatabase:
    """Authentication database manager."""

    def __init__(self):
        """Initialize database connection."""
        self.db_path = auth_config.db_path
        self._ensure_db_directory()

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection.

        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self) -> None:
        """Initialize the authentication database with schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
                    is_active BOOLEAN DEFAULT TRUE,
                    is_external BOOLEAN DEFAULT FALSE,
                    external_provider VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    access_token VARCHAR(512) UNIQUE NOT NULL,
                    refresh_token VARCHAR(512) UNIQUE NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_revoked BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Auth audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username VARCHAR(255),
                    event_type VARCHAR(50) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)

            # Login attempts table (for rate limiting)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) NOT NULL,
                    ip_address VARCHAR(45) NOT NULL,
                    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_access_token ON sessions(access_token)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_refresh_token ON sessions(refresh_token)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON auth_audit_log(user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON auth_audit_log(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)"
            )

            conn.commit()
        finally:
            conn.close()

    # User operations
    def create_user(
        self,
        username: str,
        email: str,
        password_hash: Optional[str],
        role: str = "viewer",
        is_external: bool = False,
        external_provider: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> int:
        """Create a new user.

        Args:
            username: Username
            email: Email address
            password_hash: Hashed password (None for external auth)
            role: User role (admin, developer, viewer)
            is_external: Whether user is from external auth
            external_provider: External auth provider name
            metadata: Additional user metadata

        Returns:
            int: New user ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, role, is_external, external_provider, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    username,
                    email,
                    password_hash,
                    role,
                    is_external,
                    external_provider,
                    metadata_json,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[AuthUser]: User if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[AuthUser]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            Optional[AuthUser]: User if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email.

        Args:
            email: Email address

        Returns:
            Optional[AuthUser]: User if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return self._row_to_user(row)
            return None
        finally:
            conn.close()

    def list_users(self, include_inactive: bool = False) -> List[AuthUser]:
        """List all users.

        Args:
            include_inactive: Include inactive users

        Returns:
            List[AuthUser]: List of users
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if include_inactive:
                cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            else:
                cursor.execute(
                    "SELECT * FROM users WHERE is_active = TRUE ORDER BY created_at DESC"
                )

            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]
        finally:
            conn.close()

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        password_hash: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Update user information.

        Args:
            user_id: User ID
            email: New email (optional)
            password_hash: New password hash (optional)
            role: New role (optional)
            is_active: New active status (optional)
            metadata: New metadata (optional)

        Returns:
            bool: True if updated, False if user not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            updates = []
            params = []

            if email is not None:
                updates.append("email = ?")
                params.append(email)
            if password_hash is not None:
                updates.append("password_hash = ?")
                params.append(password_hash)
            if role is not None:
                updates.append("role = ?")
                params.append(role)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))

            if not updates:
                return False

            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(user_id)

            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_user(self, user_id: int) -> bool:
        """Delete a user.

        Args:
            user_id: User ID

        Returns:
            bool: True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,),
            )
            conn.commit()
        finally:
            conn.close()

    # Session operations
    def create_session(
        self,
        user_id: int,
        access_token: str,
        refresh_token: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> int:
        """Create a new session.

        Args:
            user_id: User ID
            access_token: Access token
            refresh_token: Refresh token
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            int: Session ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            expires_at = datetime.utcnow() + timedelta(days=auth_config.refresh_token_expire_days)

            cursor.execute(
                """
                INSERT INTO sessions (user_id, access_token, refresh_token, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (user_id, access_token, refresh_token, ip_address, user_agent, expires_at),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def is_session_valid(self, access_token: str) -> bool:
        """Check if a session is valid.

        Args:
            access_token: Access token to check

        Returns:
            bool: True if valid, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT is_revoked, expires_at FROM sessions
                WHERE access_token = ?
            """,
                (access_token,),
            )
            row = cursor.fetchone()

            if not row:
                return False

            is_revoked = row["is_revoked"]
            expires_at = datetime.fromisoformat(row["expires_at"])

            return not is_revoked and expires_at > datetime.utcnow()
        finally:
            conn.close()

    def is_refresh_token_valid(self, refresh_token: str) -> bool:
        """Check if a refresh token is valid.

        Args:
            refresh_token: Refresh token to check

        Returns:
            bool: True if valid, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT is_revoked, expires_at FROM sessions
                WHERE refresh_token = ?
            """,
                (refresh_token,),
            )
            row = cursor.fetchone()

            if not row:
                return False

            is_revoked = row["is_revoked"]
            expires_at = datetime.fromisoformat(row["expires_at"])

            return not is_revoked and expires_at > datetime.utcnow()
        finally:
            conn.close()

    def update_session_access_token(self, refresh_token: str, new_access_token: str) -> bool:
        """Update access token for a session.

        Args:
            refresh_token: Refresh token
            new_access_token: New access token

        Returns:
            bool: True if updated, False if session not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE sessions
                SET access_token = ?, last_activity = CURRENT_TIMESTAMP
                WHERE refresh_token = ?
            """,
                (new_access_token, refresh_token),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_session_activity(self, access_token: str) -> None:
        """Update session last activity timestamp.

        Args:
            access_token: Access token
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE sessions
                SET last_activity = CURRENT_TIMESTAMP
                WHERE access_token = ?
            """,
                (access_token,),
            )
            conn.commit()
        finally:
            conn.close()

    def revoke_session(self, token: str) -> bool:
        """Revoke a session by access or refresh token.

        Args:
            token: Access or refresh token

        Returns:
            bool: True if revoked, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE sessions
                SET is_revoked = TRUE
                WHERE access_token = ? OR refresh_token = ?
            """,
                (token, token),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def revoke_user_sessions(self, user_id: int) -> int:
        """Revoke all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            int: Number of sessions revoked
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE sessions SET is_revoked = TRUE WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def cleanup_expired_sessions(self) -> int:
        """Delete expired sessions.

        Returns:
            int: Number of sessions deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    # Audit logging
    def log_auth_event(
        self,
        event_type: str,
        success: bool,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log an authentication event.

        Args:
            event_type: Event type (login, logout, failed_login, etc.)
            success: Whether the event was successful
            user_id: User ID (optional)
            username: Username (optional)
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            error_message: Error message if failed (optional)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    username,
                    event_type,
                    ip_address,
                    user_agent,
                    success,
                    error_message,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    # Rate limiting
    def record_login_attempt(self, username: str, ip_address: str, success: bool) -> None:
        """Record a login attempt.

        Args:
            username: Username
            ip_address: Client IP address
            success: Whether login was successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO login_attempts (username, ip_address, success)
                VALUES (?, ?, ?)
            """,
                (username, ip_address, success),
            )
            conn.commit()
        finally:
            conn.close()

    def get_failed_login_attempts(self, username: str, ip_address: str, minutes: int) -> int:
        """Get number of failed login attempts in time window.

        Args:
            username: Username
            ip_address: Client IP address
            minutes: Time window in minutes

        Returns:
            int: Number of failed attempts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            cursor.execute(
                """
                SELECT COUNT(*) FROM login_attempts
                WHERE username = ? AND ip_address = ? AND success = FALSE
                AND attempted_at > ?
            """,
                (username, ip_address, cutoff_time),
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def cleanup_old_login_attempts(self, days: int = 7) -> int:
        """Delete old login attempts.

        Args:
            days: Delete attempts older than this many days

        Returns:
            int: Number of attempts deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            cursor.execute("DELETE FROM login_attempts WHERE attempted_at < ?", (cutoff_time,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    # Helper methods
    def _row_to_user(self, row: sqlite3.Row) -> AuthUser:
        """Convert database row to AuthUser object.

        Args:
            row: Database row

        Returns:
            AuthUser: User object
        """
        metadata = json.loads(row["metadata"]) if row["metadata"] else None

        last_login = None
        if row["last_login"]:
            last_login = datetime.fromisoformat(row["last_login"])

        return AuthUser(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            is_external=bool(row["is_external"]),
            external_provider=row["external_provider"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_login=last_login,
            metadata=metadata,
        )


# Global database instance
_auth_db: Optional[AuthDatabase] = None


def get_auth_db() -> AuthDatabase:
    """Get the global auth database instance.

    Returns:
        AuthDatabase: Auth database instance
    """
    global _auth_db
    if _auth_db is None:
        _auth_db = AuthDatabase()
    return _auth_db


def init_auth_database() -> None:
    """Initialize the authentication database."""
    db = get_auth_db()
    db.initialize_database()
