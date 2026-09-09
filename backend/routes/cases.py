"""
backend/routes/cases.py — Project DRISHTI
=========================================
REST API endpoints for Cybercrime Investigation Case Management,
Timeline Audits, Verified Field Outcome Reporting, and Feedback Retraining.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from backend.auth.security import get_current_user
from backend.services.case_service import CaseService, get_case_service


router = APIRouter(prefix="/cases", tags=["Investigation Cases"])


# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="NEW | ANALYZING | HIGH_PRIORITY | ACTION_REQUIRED | FIELD_ACTION | RESOLVED | CLOSED")
    note: Optional[str] = Field(None, description="Investigator operational note")


class AssignInvestigatorRequest(BaseModel):
    investigator: str = Field(..., description="Investigator username or badge identifier")


class OutcomeReportRequest(BaseModel):
    actual_atm_id: str = Field(..., description="Actual ATM terminal where suspect attempted cash-out")
    actual_time: Optional[str] = Field(None, description="ISO-8601 timestamp of verified cash-out attempt")
    actual_amount: float = Field(..., ge=0.0, description="Actual cash amount withdrawn or intercepted")
    was_intercepted: bool = Field(False, description="Whether law enforcement physically or digitally intercepted the funds")
    is_correct: bool = Field(True, description="Investigator confirmation of prediction correctness")
    notes: Optional[str] = Field(None, description="Field arrest and evidence summary")


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get Command Center KPI summary statistics",
)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """
    Returns live dynamic KPI metrics derived directly from the cases table
    and verified outcomes. No hardcoded or fake metrics.
    """
    return case_service.get_stats()


@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="List investigation cases with optional filters",
)
async def list_cases(
    status: Optional[str] = Query(None, description="Filter by case status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier (LOW, MEDIUM, HIGH, CRITICAL)"),
    search: Optional[str] = Query(None, description="Search by Case ID, Complaint ID, Area, or Investigator"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """Lists investigation dossiers ordered by composite priority score."""
    return case_service.list_cases(
        status=status,
        risk_level=risk_level,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{case_id}",
    response_model=Dict[str, Any],
    summary="Get complete investigation case dossier",
)
async def get_case_detail(
    case_id: str,
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """Retrieves full case details including money trail, predictions, feasibility, and 5D intelligence."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case '{case_id}' not found.",
        )
    return case


@router.get(
    "/{case_id}/timeline",
    response_model=List[Dict[str, Any]],
    summary="Get chronological timeline of events for an investigation",
)
async def get_case_timeline(
    case_id: str,
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """Returns all timeline events recorded from complaint intake to resolution."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case '{case_id}' not found.",
        )
    return case_service.get_timeline(case_id)


@router.patch(
    "/{case_id}/status",
    response_model=Dict[str, Any],
    summary="Update case status and log timeline transition",
)
async def update_case_status(
    case_id: str,
    payload: StatusUpdateRequest,
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """Updates case status and creates an auditable timeline record."""
    valid_statuses = {"NEW", "ANALYZING", "HIGH_PRIORITY", "ACTION_REQUIRED", "FIELD_ACTION", "RESOLVED", "CLOSED"}
    st_clean = payload.status.strip().upper()
    if st_clean not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{payload.status}'. Valid choices: {sorted(list(valid_statuses))}",
        )

    updated = case_service.update_status(
        case_id=case_id,
        status=st_clean,
        user=current_user.get("username", "INVESTIGATOR"),
        note=payload.note,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )
    return updated


@router.patch(
    "/{case_id}/assign",
    response_model=Dict[str, Any],
    summary="Assign case to an investigator",
)
async def assign_case(
    case_id: str,
    payload: AssignInvestigatorRequest,
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """Assigns an investigator to the case dossier."""
    # RBAC check: only admin or analyst can assign cases
    user_role = current_user.get("role", "investigator")
    if user_role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only administrators and analysts can assign cases.",
        )

    updated = case_service.assign_investigator(
        case_id=case_id,
        investigator=payload.investigator,
        user=current_user.get("username", "SYSTEM"),
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )
    return updated


@router.post(
    "/{case_id}/outcome",
    response_model=Dict[str, Any],
    summary="Record verified field outcome and evaluate prediction accuracy",
)
async def record_case_outcome(
    case_id: str,
    payload: OutcomeReportRequest,
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """
    Submits ground truth from field operations.
    Automatically computes:
      - Location Accuracy
      - Time Window Accuracy
      - Amount Absolute Error
      - Top-K Hit Rate
      - Overall Success
    Saves feedback sample for candidate model retraining.
    """
    outcome_dict = payload.model_dump()
    updated = case_service.record_outcome(
        case_id=case_id,
        outcome_data=outcome_dict,
        user=current_user.get("username", "INVESTIGATOR"),
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )
    return updated


@router.post(
    "/candidate-retrain",
    response_model=Dict[str, Any],
    summary="Trigger candidate model retraining pipeline with promotion gate",
)
async def retrain_candidate_model(
    current_user: dict = Depends(get_current_user),
    case_service: CaseService = Depends(get_case_service),
):
    """
    Evaluates candidate model on collected field outcome feedback.
    Promotes to production ONLY if candidate performance strictly exceeds baseline.
    Requires ADMIN or ANALYST role.
    """
    role = current_user.get("role", "investigator")
    if role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Candidate retraining pipeline requires ADMIN or ANALYST privileges.",
        )
    return case_service.evaluate_and_retrain_candidate(user=current_user.get("username", "admin"))
