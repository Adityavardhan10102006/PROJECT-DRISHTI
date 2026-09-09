"""
backend/repositories/audit_repository.py — Project DRISHTI
==========================================================
Repository layer for immutable security and operational audit logs.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import SessionLocal, AuditLog


class AuditRepository:
    """
    Manages persistence and retrieval of AuditLog entries.
    Ensures that security events, predictions, and case lifecycle operations
    are non-repudiable and auditable.
    """

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def log(
        self,
        user: str,
        action: str,
        case_id: Optional[str] = None,
        result: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Appends an immutable audit log entry."""
        db: Session = self.session_factory()
        try:
            entry = AuditLog(
                user=user.strip() if user else "SYSTEM",
                action=action.strip().upper(),
                case_id=case_id.strip() if case_id else None,
                timestamp=datetime.now(timezone.utc),
                result=result.strip().upper(),
                details=details or {},
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        finally:
            db.close()

    def list_logs(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        case_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Queries audit log entries ordered newest first."""
        db: Session = self.session_factory()
        try:
            q = db.query(AuditLog)
            if user:
                q = q.filter(AuditLog.user == user.strip())
            if action:
                q = q.filter(AuditLog.action == action.strip().upper())
            if case_id:
                q = q.filter(AuditLog.case_id == case_id.strip())
            return q.order_by(desc(AuditLog.timestamp), desc(AuditLog.id)).offset(offset).limit(limit).all()
        finally:
            db.close()

    def count_logs(self) -> int:
        """Returns total audit log entries count."""
        db: Session = self.session_factory()
        try:
            return db.query(AuditLog).count()
        finally:
            db.close()
