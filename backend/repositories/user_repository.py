"""
backend/repositories/user_repository.py — Project DRISHTI
==========================================================
Repository layer for User accounts and authentication entities.
Decouples database session lifecycle and queries from business logic.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.auth.user_model import User


class UserRepository:
    """
    Encapsulates persistence and retrieval operations for User accounts.

    Encapsulation:
      - Manages database sessions cleanly.
      - Never leaks raw credentials or session objects to callers.
    """

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def find_by_username(self, username: str) -> Optional[User]:
        """Finds active user by username (case-insensitive)."""
        if not username:
            return None
        db: Session = self.session_factory()
        try:
            return (
                db.query(User)
                .filter(
                    User.username == username.strip().lower(),
                    User.is_active == True,
                )
                .first()
            )
        finally:
            db.close()

    def find_by_email(self, email: str) -> Optional[User]:
        """Finds active user by email address."""
        if not email:
            return None
        db: Session = self.session_factory()
        try:
            return (
                db.query(User)
                .filter(
                    User.email == email.strip().lower(),
                    User.is_active == True,
                )
                .first()
            )
        finally:
            db.close()

    def find_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Finds active user by username OR email."""
        if not identifier:
            return None
        ident = identifier.strip().lower()
        db: Session = self.session_factory()
        try:
            return (
                db.query(User)
                .filter(
                    (User.username == ident) | (User.email == ident),
                    User.is_active == True,
                )
                .first()
            )
        finally:
            db.close()

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Finds active user by primary key ID."""
        db: Session = self.session_factory()
        try:
            return db.query(User).filter(User.id == user_id, User.is_active == True).first()
        finally:
            db.close()

    def save(self, user: User) -> User:
        """Persists or updates a user entity."""
        db: Session = self.session_factory()
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update_last_login(self, user_id: int, dt: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Updates last_login timestamp and returns safe user dict."""
        now = dt or datetime.now(timezone.utc)
        db: Session = self.session_factory()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = now
                db.commit()
                db.refresh(user)
                return user.to_safe_dict()
            return None
        except Exception:
            db.rollback()
            return None
        finally:
            db.close()

    def list_all(self, active_only: bool = True) -> List[User]:
        """Returns list of users."""
        db: Session = self.session_factory()
        try:
            q = db.query(User)
            if active_only:
                q = q.filter(User.is_active == True)
            return q.all()
        finally:
            db.close()
