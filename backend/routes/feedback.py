"""
backend/routes/feedback.py — Project DRISHTI
==============================================
Outcome Validation & Continuous Improvement API.

Endpoints:
  - POST /alerts/{complaint_id}/outcome : Log officer field outcome
  - GET  /alerts/feedback/stats         : Cumulative accuracy and INR recovery metrics
  - POST /alerts/feedback/retrain       : Continuous retraining trigger
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/alerts", tags=["Outcome Validation"])

FEEDBACK_LOG_PATH = "data/feedback_store.jsonl"
os.makedirs("data", exist_ok=True)


class FeedbackIn(BaseModel):
    complaint_id: str = Field(..., description="ID of the alert being validated")
    was_intercepted: bool = Field(..., description="Did police physically intercept or freeze funds in time?")
    location_accurate: bool = Field(..., description="Was cash-out at predicted ATM or nearby cluster?")
    time_window_accurate: bool = Field(..., description="Did cash-out occur within the predicted window?")
    mule_confirmed: bool = Field(..., description="Was flagged account confirmed as a mule?")
    actual_withdrawal_minutes: Optional[int] = Field(None, description="Actual minutes from complaint to cash-out")
    recovered_amount: Optional[float] = Field(None, description="Amount in INR successfully preserved/intercepted")
    officer_badge: Optional[str] = Field("POLICE-SIH-01", description="Validating officer badge/ID")
    notes: Optional[str] = Field(None, description="Field notes / arrest details")


class FeedbackStats(BaseModel):
    total_validations: int
    interceptions_count: int
    interception_success_rate: float
    location_accuracy_rate: float
    time_window_accuracy_rate: float
    mule_confirmation_rate: float
    total_recovered_amount: float
    last_updated: datetime


def _load_all_feedbacks() -> List[Dict[str, Any]]:
    if not os.path.exists(FEEDBACK_LOG_PATH):
        return []
    feedbacks = []
    with open(FEEDBACK_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    feedbacks.append(json.loads(line))
                except Exception:
                    continue
    return feedbacks


@router.post(
    "/{complaint_id}/outcome",
    status_code=status.HTTP_201_CREATED,
    summary="Submit ground-truth outcome feedback for a prediction alert",
    description="Records whether police intercepted the suspect, location/time accuracy, and funds recovered."
)
async def submit_alert_outcome(complaint_id: str, feedback: FeedbackIn):
    if feedback.complaint_id != complaint_id:
        feedback.complaint_id = complaint_id

    record = feedback.model_dump()
    record["logged_at"] = datetime.utcnow().isoformat()

    # Append to JSONL file
    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {
        "status": "success",
        "message": f"Outcome validation logged for alert {complaint_id}",
        "feedback_logged": record,
    }


@router.get(
    "/feedback/stats",
    response_model=FeedbackStats,
    summary="Get cumulative validation statistics and recovery metrics",
)
async def get_feedback_stats():
    records = _load_all_feedbacks()
    if not records:
        return FeedbackStats(
            total_validations=0,
            interceptions_count=0,
            interception_success_rate=0.0,
            location_accuracy_rate=0.0,
            time_window_accuracy_rate=0.0,
            mule_confirmation_rate=0.0,
            total_recovered_amount=0.0,
            last_updated=datetime.utcnow(),
        )

    n = len(records)
    intercepted = sum(1 for r in records if r.get("was_intercepted"))
    loc_acc = sum(1 for r in records if r.get("location_accurate"))
    time_acc = sum(1 for r in records if r.get("time_window_accurate"))
    mule_acc = sum(1 for r in records if r.get("mule_confirmed"))
    recovered = sum(float(r.get("recovered_amount") or 0.0) for r in records)

    return FeedbackStats(
        total_validations=n,
        interceptions_count=intercepted,
        interception_success_rate=round(intercepted / n, 3),
        location_accuracy_rate=round(loc_acc / n, 3),
        time_window_accuracy_rate=round(time_acc / n, 3),
        mule_confirmation_rate=round(mule_acc / n, 3),
        total_recovered_amount=round(recovered, 2),
        last_updated=datetime.utcnow(),
    )


@router.post(
    "/feedback/retrain",
    summary="Trigger model retraining incorporating accumulated feedback",
)
async def trigger_retraining():
    from backend.ml.retrain_feedback import run_continuous_retraining
    result = run_continuous_retraining()
    return result
