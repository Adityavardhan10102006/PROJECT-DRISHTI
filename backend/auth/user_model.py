"""
backend/auth/user_model.py — Project DRISHTI
============================================
SQLAlchemy User model for authentication.

Stored in the same SQLite database as Alert (data/drishti.db).
Passwords are NEVER stored in plaintext — only bcrypt hashes.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from backend.database import Base


class User(Base):
    """
    User account for DRISHTI platform authentication.

    Roles:
      - admin:        Full access, can trigger retraining, manage system
      - analyst:      Can submit complaints, view predictions, log outcomes
      - investigator: Read-only access to predictions (future use)

    Password storage:
      - password_hash: bcrypt hash (NEVER plaintext)
      - The raw password is NEVER stored or returned by any API
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="analyst", nullable=False)  # admin | analyst | investigator
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login = Column(DateTime, nullable=True)

    def to_safe_dict(self) -> Dict[str, Any]:
        """
        Return a safe dict representation — NEVER includes password_hash.
        Used for API responses and JWT payload.
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"
