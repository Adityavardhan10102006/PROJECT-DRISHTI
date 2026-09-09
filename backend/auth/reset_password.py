"""
backend/auth/reset_password.py — Project DRISHTI
=================================================
Admin utility to reset a user's password via command line.

Usage:
    python -m backend.auth.reset_password
    python -m backend.auth.reset_password --username admin --password NewPass@123

This script is intentionally NOT an API endpoint.
Password resets MUST be performed by a system administrator with server access.
"""

import os
import sys
import getpass
import argparse

# Ensure the project root is in Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def reset_password(username: str, new_password: str) -> bool:
    """
    Reset the password for a given username.

    Args:
        username:     The username to reset
        new_password: The new plaintext password (will be bcrypt-hashed)

    Returns:
        True if reset succeeded, False otherwise
    """
    from backend.database import SessionLocal, init_db
    from backend.auth.user_model import User
    from backend.auth.security import hash_password

    init_db()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username.strip().lower()).first()
        if not user:
            print(f"[ERROR] User '{username}' not found in database.")
            return False

        user.password_hash = hash_password(new_password)
        db.commit()
        print(f"[OK] Password for user '{username}' has been reset successfully.")
        print(f"[OK] The new password hash has been stored securely (bcrypt).")
        return True
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Password reset failed: {exc}")
        return False
    finally:
        db.close()


def list_users() -> None:
    """List all users in the database (for admin reference)."""
    from backend.database import SessionLocal, init_db
    from backend.auth.user_model import User

    init_db()
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("No users found in database.")
            return
        print(f"\n{'ID':<5} {'Username':<20} {'Role':<15} {'Active':<8} {'Last Login'}")
        print("-" * 65)
        for u in users:
            last_login = u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "Never"
            print(f"{u.id:<5} {u.username:<20} {u.role:<15} {str(u.is_active):<8} {last_login}")
        print()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="DRISHTI Admin: Reset user password",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m backend.auth.reset_password\n"
            "  python -m backend.auth.reset_password --username admin --password NewPass@123\n"
            "  python -m backend.auth.reset_password --list\n"
        ),
    )
    parser.add_argument("--username", "-u", help="Username to reset", default=None)
    parser.add_argument("--password", "-p", help="New password (prompted if omitted)", default=None)
    parser.add_argument("--list", "-l", action="store_true", help="List all users")

    args = parser.parse_args()

    print("\n[DRISHTI] Admin Password Reset Utility")
    print("=" * 40)

    if args.list:
        list_users()
        return

    # Get username
    username = args.username
    if not username:
        list_users()
        username = input("Enter username to reset: ").strip()
        if not username:
            print("[ERROR] Username is required.")
            sys.exit(1)

    # Get new password (never echoed to terminal)
    new_password = args.password
    if not new_password:
        new_password = getpass.getpass(f"Enter new password for '{username}': ")
        confirm = getpass.getpass("Confirm new password: ")
        if new_password != confirm:
            print("[ERROR] Passwords do not match.")
            sys.exit(1)

    if len(new_password) < 8:
        print("[ERROR] Password must be at least 8 characters.")
        sys.exit(1)

    success = reset_password(username, new_password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
