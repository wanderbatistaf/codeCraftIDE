#!/usr/bin/env python3
"""Initialize authentication system for fglInterpreter.

This script:
1. Initializes the authentication database
2. Creates an initial admin user
3. Verifies the setup

Usage:
    python scripts/init_auth.py
"""

import getpass
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fglinterpreter.api.auth.config import auth_config
from fglinterpreter.api.auth.core.security import hash_password, validate_password_strength
from fglinterpreter.api.auth.database import AuthDatabase, init_auth_database


def print_header():
    """Print setup header."""
    print("=" * 70)
    print("fglInterpreter Authentication System Setup")
    print("=" * 70)
    print()


def print_config():
    """Print current configuration."""
    print("Current Configuration:")
    print(f"  Auth Enabled: {auth_config.enabled}")
    print(f"  Strategy: {auth_config.strategy}")
    print(f"  Database: {auth_config.db_type}")
    print(f"  Database Path: {auth_config.db_path}")
    print()


def create_admin_user(db: AuthDatabase) -> bool:
    """Create initial admin user.

    Args:
        db: Auth database instance

    Returns:
        bool: True if successful, False otherwise
    """
    print("Creating Initial Admin User")
    print("-" * 70)
    print()

    # Get username
    while True:
        username = input("Admin username (min 3 characters): ").strip()
        if len(username) >= 3:
            break
        print("Username must be at least 3 characters long!")

    # Check if username already exists
    existing = db.get_user_by_username(username)
    if existing:
        print(f"\nError: Username '{username}' already exists!")
        return False

    # Get email
    while True:
        email = input("Admin email: ").strip()
        if "@" in email and "." in email:
            break
        print("Please enter a valid email address!")

    # Check if email already exists
    existing_email = db.get_user_by_email(email)
    if existing_email:
        print(f"\nError: Email '{email}' already exists!")
        return False

    # Get password
    while True:
        password = getpass.getpass("Admin password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            print("Passwords do not match! Try again.")
            continue

        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            print(f"\n{error_message}")
            print("Try again.")
            continue

        break

    # Hash password
    password_hash = hash_password(password)

    # Create user
    try:
        user_id = db.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            role="admin",
            is_external=False,
            external_provider=None,
        )

        print()
        print("✓ Admin user created successfully!")
        print(f"  User ID: {user_id}")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print("  Role: admin")
        print()
        return True

    except Exception as e:
        print(f"\nError creating user: {e}")
        return False


def verify_setup(db: AuthDatabase) -> None:
    """Verify the setup.

    Args:
        db: Auth database instance
    """
    print("Verifying Setup")
    print("-" * 70)
    print()

    # Count users
    users = db.list_users(include_inactive=True)
    print(f"✓ Total users in database: {len(users)}")

    # List admin users
    admin_users = [u for u in users if u.role == "admin"]
    print(f"✓ Admin users: {len(admin_users)}")
    for user in admin_users:
        print(f"  - {user.username} ({user.email})")

    print()


def print_next_steps():
    """Print next steps."""
    print("Next Steps")
    print("-" * 70)
    print()
    print("1. Set AUTH_ENABLED=true in your .env file to enable authentication")
    print()
    print("2. Set a secure JWT_SECRET_KEY in your .env file:")
    print("   Generate with: openssl rand -hex 32")
    print('   Or use: python -c "import secrets; print(secrets.token_hex(32))"')
    print()
    print("3. Restart the backend server:")
    print("   uvicorn fglinterpreter.api.main:app --reload")
    print()
    print("4. Login with your admin credentials at:")
    print("   http://localhost:8000/api/docs (FastAPI docs)")
    print("   or through the IDE frontend")
    print()
    print("5. (Optional) Create additional users via:")
    print("   - Admin UI in the IDE")
    print("   - POST /api/users endpoint")
    print()


def main():
    """Main setup function."""
    print_header()
    print_config()

    # Warn if auth is currently enabled
    if auth_config.enabled:
        print("⚠ Warning: Authentication is currently ENABLED")
        print("  This script will initialize the database.")
        print("  Make sure the backend server is not running.")
        print()
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Setup cancelled.")
            return
        print()

    # Initialize database
    print("Initializing Authentication Database")
    print("-" * 70)
    print()

    try:
        init_auth_database()
        print(f"✓ Database initialized at: {auth_config.db_path}")
        print()
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

    # Create database instance
    db = AuthDatabase()

    # Check if admin user already exists
    users = db.list_users(include_inactive=True)
    admin_users = [u for u in users if u.role == "admin"]

    if admin_users:
        print("Note: Admin user(s) already exist:")
        for user in admin_users:
            print(f"  - {user.username} ({user.email})")
        print()
        response = input("Create another admin user? (yes/no): ")
        if response.lower() != "yes":
            verify_setup(db)
            print_next_steps()
            return
        print()

    # Create admin user
    if not create_admin_user(db):
        print("Setup failed!")
        sys.exit(1)

    # Verify setup
    verify_setup(db)

    # Print next steps
    print_next_steps()

    print("=" * 70)
    print("Setup Complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
