"""
backend/routes/audit.py — Project DRISHTI
=========================================
REST API endpoints for Security and Operational Audit Logs.
Enforces Role-Based Access Control (Admin / Analyst only).
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query

from backend.auth.security import get_current_user
from backend.repositories.audit_repository import AuditRepository


router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])
_audit_repo = AuditRepository()


@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="Query audit logs (Admin / Analyst only)",
)
async def list_audit_logs(
    user: Optional[str] = Query(None, description="Filter by user"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns security audit log events.
    Enforces Role-Based Access Control: strictly restricted to Admin and Analyst roles.
    """
    role = current_user.get("role", "investigator")
    if role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Audit logs may only be viewed by administrators or analysts.",
        )

    logs = _audit_repo.list_logs(
        user=user,
        action=action,
        case_id=case_id,
        limit=limit,
        offset=offset,
    )
    return [entry.to_dict() for entry in logs]
