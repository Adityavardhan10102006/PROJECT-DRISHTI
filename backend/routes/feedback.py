"""
backend/routes/feedback.py — Project DRISHTI
==============================================
Outcome Validation, SQLite Alert Tracking & Asynchronous Retraining API.

Endpoints:
  - POST /alerts/{id}/outcome     : Update SQLite alert status and log officer outcome
  - GET  /alerts/feedback/stats   : Cumulative accuracy and INR recovery metrics
  - POST /alerts/feedback/retrain : Asynchronous retraining trigger (Protected by X-API-Key, returns 202 Accepted)
  - GET  /retrain/status/{task_id}: Poll retraining task status (PENDING, RUNNING, COMPLETED, FAILED)
  - GET  /alerts/{id}             : Fetch alert record by alert_id or complaint_id
  - GET  /alerts/                 : List recent alerts from SQLite
"""

import os
import json
import uuid
import threading
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Header, status, Depends
from pydantic import BaseModel, Field

from backend.database import SessionLocal, Alert
from backend.auth.security import get_current_user

load_dotenv()

router = APIRouter(tags=["Outcome Validation & Retraining"])

FEEDBACK_LOG_PATH = "data/feedback_store.jsonl"
os.makedirs("data", exist_ok=True)


# ─────────────────────────────────────────────
# BACKGROUND THREAD POOL & TASK REGISTRY
# ─────────────────────────────────────────────

class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Bounded single-worker thread pool:
# Gradient boosting retraining is CPU-bound; keeping max_workers=1 prevents
# resource starvation on low-spec laptops while offloading work off the event loop.
RETRAIN_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="drishti-retrain-")

# Thread-safe in-memory task registry
TASKS_LOCK = threading.Lock()
TASKS: Dict[str, Dict[str, Any]] = {}


def retrain_model() -> Dict[str, Any]:
    """Execute continuous retraining loop using collected field feedback."""
    from backend.ml.retrain_feedback import run_continuous_retraining
    return run_continuous_retraining()


def _execute_retraining_task(task_id: str):
    """
    Worker function executed in the background thread pool.
    Transitions task state: PENDING -> RUNNING -> COMPLETED (or FAILED).
    """
    with TASKS_LOCK:
        if task_id in TASKS:
            TASKS[task_id]["status"] = TaskState.RUNNING.value
            TASKS[task_id]["started_at"] = datetime.now(timezone.utc).isoformat()

    try:
        result = retrain_model()
        with TASKS_LOCK:
            if task_id in TASKS:
                TASKS[task_id]["status"] = TaskState.COMPLETED.value
                TASKS[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                TASKS[task_id]["result"] = result
    except Exception as exc:
        with TASKS_LOCK:
            if task_id in TASKS:
                TASKS[task_id]["status"] = TaskState.FAILED.value
                TASKS[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                TASKS[task_id]["error"] = str(exc)


# ─────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────

class FeedbackIn(BaseModel):
    complaint_id: Optional[str] = Field(None, description="ID of the alert or complaint being validated")
    was_intercepted: bool = Field(..., description="Did police physically intercept or freeze funds in time?")
    location_accurate: bool = Field(..., description="Was cash-out at predicted ATM or nearby cluster?")
    time_window_accurate: bool = Field(..., description="Did cash-out occur within the predicted window?")
    mule_confirmed: bool = Field(..., description="Was flagged account confirmed as a mule?")
    status: Optional[str] = Field(None, description="Explicit alert status: PENDING, DISPATCHED, INTERCEPTED, FAILED")
    actual_withdrawal_minutes: Optional[int] = Field(None, description="Actual minutes from complaint to cash-out")
    recovered_amount: Optional[float] = Field(None, description="Amount in INR successfully preserved/intercepted")
    officer_badge: Optional[str] = Field("POLICE-IND-01", description="Validating officer badge/ID")
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


class RetrainTaskResponse(BaseModel):
    status: str
    task_id: str
    message: str
    status_url: str


class RetrainStatusResponse(BaseModel):
    task_id: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


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


# ─────────────────────────────────────────────
# STATIC & ASYNC RETRAINING ROUTES
# ─────────────────────────────────────────────

@router.get(
    "/alerts/feedback/stats",
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
            last_updated=datetime.now(timezone.utc),
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
        last_updated=datetime.now(timezone.utc),
    )


@router.post(
    "/alerts/feedback/retrain",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RetrainTaskResponse,
    summary="Trigger model retraining asynchronously in a background thread (API Key Protected)",
    description="Submits retraining task to background ThreadPoolExecutor and returns 202 Accepted with a task_id.",
)
async def trigger_retraining(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key", description="Admin API Key header")
):
    admin_api_key = os.getenv("ADMIN_API_KEY")
    if not admin_api_key or x_api_key != admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or missing API key. Provide valid 'X-API-Key' header."
        )

    task_id = f"retrain_{uuid.uuid4().hex[:12]}"
    now_str = datetime.now(timezone.utc).isoformat()

    task_record = {
        "task_id": task_id,
        "status": TaskState.PENDING.value,
        "created_at": now_str,
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
    }

    with TASKS_LOCK:
        TASKS[task_id] = task_record

    # Offload retraining to background thread pool
    RETRAIN_EXECUTOR.submit(_execute_retraining_task, task_id)

    return RetrainTaskResponse(
        status=TaskState.PENDING.value,
        task_id=task_id,
        message="Model retraining task submitted asynchronously to background thread pool.",
        status_url=f"/retrain/status/{task_id}",
    )


@router.get(
    "/retrain/status/{task_id}",
    response_model=RetrainStatusResponse,
    summary="Check current state of asynchronous retraining task",
    description="Returns current state: PENDING, RUNNING, COMPLETED, or FAILED.",
)
@router.get(
    "/alerts/retrain/status/{task_id}",
    response_model=RetrainStatusResponse,
    include_in_schema=False,
)
@router.get(
    "/alerts/feedback/retrain/status/{task_id}",
    response_model=RetrainStatusResponse,
    include_in_schema=False,
)
async def get_retrain_status(task_id: str):
    with TASKS_LOCK:
        task_info = TASKS.get(task_id)

    if not task_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retraining task '{task_id}' not found."
        )

    return RetrainStatusResponse(**task_info)


@router.get(
    "/alerts/",
    summary="List recent alerts stored in SQLite database",
)
@router.get(
    "/alerts",
    include_in_schema=False,
)
async def list_alerts(limit: int = 50):
    with SessionLocal() as db:
        alerts = db.query(Alert).order_by(Alert.id.desc()).limit(limit).all()
        return [a.to_dict() for a in alerts]


# ─────────────────────────────────────────────
# PARAMETERIZED ROUTES (/alerts/{id})
# ─────────────────────────────────────────────

@router.get(
    "/alerts/{id}",
    summary="Get alert details by alert_id or complaint_id",
)
async def get_alert(id: str):
    with SessionLocal() as db:
        db_alert = None
        if id.isdigit():
            db_alert = db.query(Alert).filter(Alert.id == int(id)).first()
        if not db_alert:
            db_alert = db.query(Alert).filter(Alert.complaint_id == id).first()
        if not db_alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with id or complaint_id '{id}' not found."
            )
        return db_alert.to_dict()


@router.post(
    "/alerts/{id}/outcome",
    status_code=status.HTTP_201_CREATED,
    summary="Submit ground-truth outcome feedback for a prediction alert",
    description="Updates SQLite Alert status (PENDING, DISPATCHED, INTERCEPTED, FAILED) based on alert_id and logs outcome."
)
async def submit_alert_outcome(id: str, feedback: FeedbackIn, current_user: dict = Depends(get_current_user)):
    # Determine new alert status
    if feedback.status:
        new_status = feedback.status.upper()
    elif feedback.was_intercepted:
        new_status = "INTERCEPTED"
    else:
        new_status = "FAILED"

    valid_statuses = {"PENDING", "DISPATCHED", "INTERCEPTED", "FAILED"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'. Allowed values: {', '.join(sorted(valid_statuses))}"
        )

    # 1. Update Alert record in persistent SQLite database
    alert_dict = None
    with SessionLocal() as db:
        db_alert = None
        if id.isdigit():
            db_alert = db.query(Alert).filter(Alert.id == int(id)).first()
        if not db_alert:
            db_alert = db.query(Alert).filter(Alert.complaint_id == id).first()

        if not db_alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with id or complaint_id '{id}' not found."
            )

        db_alert.status = new_status
        db.commit()
        db.refresh(db_alert)
        alert_dict = db_alert.to_dict()

        # Ensure complaint_id on feedback record matches
        if not feedback.complaint_id:
            feedback.complaint_id = db_alert.complaint_id

    # 2. Append to JSONL audit log
    record = feedback.model_dump()
    record["alert_id"] = alert_dict["id"]
    record["status"] = new_status
    record["logged_at"] = datetime.now(timezone.utc).isoformat()

    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {
        "status": "success",
        "message": f"Alert {alert_dict['id']} ({alert_dict['complaint_id']}) status updated to {new_status}",
        "alert": alert_dict,
        "feedback_logged": record,
    }
