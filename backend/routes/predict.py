"""
backend/routes/predict.py — Project DRISHTI
============================================
POST /predict endpoint.
Thin API Route Controller delegating full intelligence orchestration
to DrishtiIntelligenceService.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends

from backend.auth.security import get_current_user
from backend.domain.complaint import Complaint
from backend.services.drishti_service import DrishtiIntelligenceService, get_drishti_service
from backend.models import (
    ComplaintIn,
    PredictionOut,
    TimeWindow,
)

router = APIRouter(prefix="/predict", tags=["Prediction"])

_time_model = None


def _get_time_model():
    """
    Lazy-load the XGBoost predictor so the server still starts even if the
    model file hasn't been trained yet (returns None -> falls back to rules).
    Maintained for startup lifespan pre-warming.
    """
    global _time_model
    if _time_model is not None:
        return _time_model
    try:
        from backend.ml.time_predictor import TimeWindowPredictor
        _time_model = TimeWindowPredictor()
    except FileNotFoundError as e:
        print(f"[DRISHTI] XGBoost model not found ({e}). Using rule-based fallback.")
        _time_model = None
    except Exception as e:
        print(f"[DRISHTI] XGBoost load error: {e}. Using rule-based fallback.")
        _time_model = None
    return _time_model


_RULE_WINDOWS = {
    "upi_fraud": (20, 60, 35),
    "kyc_fraud": (10, 50, 25),
    "phishing":  (35, 90, 55),
}


def _rule_based_window(fraud_type: str) -> TimeWindow:
    earliest, latest, peak = _RULE_WINDOWS.get(fraud_type, (20, 80, 40))
    return TimeWindow(
        earliest_minutes=earliest,
        latest_minutes=latest,
        peak_minutes=peak,
        confidence=0.50,
    )


def compute_alert_level(amount: float, fraud_type: str, peak_minutes: int = 40) -> str:
    """Urgency = f(amount, time remaining)."""
    if amount >= 100000 or (amount >= 50000 and peak_minutes <= 30):
        return "CRITICAL"
    elif amount >= 25000:
        return "HIGH"
    elif amount >= 5000:
        return "MEDIUM"
    return "LOW"


_CITY_BOUNDS = {
    "Mumbai":    (18.87, 19.27, 72.77, 72.99),
    "Delhi":     (28.40, 28.88, 76.84, 77.35),
    "Bangalore": (12.83, 13.14, 77.46, 77.78),
    "Hyderabad": (17.28, 17.55, 78.35, 78.60),
    "Chennai":   (12.90, 13.23, 80.15, 80.30),
    "Kolkata":   (22.45, 22.65, 88.30, 88.48),
    "Pune":      (18.43, 18.63, 73.77, 73.97),
    "Ahmedabad": (22.95, 23.12, 72.53, 72.68),
    "Jaipur":    (26.83, 26.98, 75.74, 75.90),
    "Lucknow":   (26.78, 26.96, 80.87, 81.05),
}


def _infer_city(lat: Optional[float], lon: Optional[float]) -> str:
    if lat is None or lon is None:
        return "Unknown"
    for city, (lat_min, lat_max, lon_min, lon_max) in _CITY_BOUNDS.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return city
    return "Unknown"


# ─────────────────────────────────────────────
# POST /predict — Thin API Route Controller
# ─────────────────────────────────────────────
@router.post(
    "/",
    response_model=PredictionOut,
    status_code=status.HTTP_200_OK,
    summary="Submit a cybercrime complaint for hotspot + time-window prediction",
    description=(
        "Returns:\n"
        "- **hotspot / top_k_locations**: Ranked candidate ATM terminals\n"
        "- **time_window**: XGBoost-predicted minutes-to-withdrawal window\n"
        "- **money_trail**: Multi-hop NetworkX laundering chain\n"
        "- **five_d**: Structured 5D Actionable Intelligence\n"
    ),
)
async def predict(
    complaint: ComplaintIn,
    current_user: dict = Depends(get_current_user),
    service: DrishtiIntelligenceService = Depends(get_drishti_service),
) -> PredictionOut:
    """
    Thin Route Controller:
      1. Validates HTTP inputs (ranges, format)
      2. Instantiates domain Complaint model
      3. Calls DrishtiIntelligenceService orchestrator facade
      4. Returns structured PredictionOut response
    """
    # 1. Coordinate and Amount Validation
    if complaint.victim_lat is not None and not (-90.0 <= float(complaint.victim_lat) <= 90.0):
        raise HTTPException(status_code=422, detail="Invalid coordinates: victim_lat must be between -90 and 90.")
    if complaint.victim_lon is not None and not (-180.0 <= float(complaint.victim_lon) <= 180.0):
        raise HTTPException(status_code=422, detail="Invalid coordinates: victim_lon must be between -180 and 180.")
    if complaint.amount is not None and float(complaint.amount) < 0:
        raise HTTPException(status_code=422, detail="Invalid amount: amount must be greater than or equal to 0.")

    # 2. Build domain Complaint entity
    cid = complaint.complaint_id or f"DRISHTI-{uuid.uuid4().hex[:8].upper()}"
    fraud_type_str = (complaint.fraud_type.value if hasattr(complaint.fraud_type, "value") else str(complaint.fraud_type)) if complaint.fraud_type else "upi_fraud"

    domain_complaint = Complaint(
        case_id=cid,
        complaint_text=complaint.complaint_text,
        fraud_type=fraud_type_str,
        amount=float(complaint.amount) if complaint.amount is not None else 0.0,
        timestamp=complaint.timestamp,
        victim_lat=complaint.victim_lat,
        victim_lon=complaint.victim_lon,
        bank_account=complaint.bank_account,
        transaction_id=complaint.transaction_id,
        ifsc_code=complaint.ifsc_code,
    )

    # 3. Analyze via orchestrator service
    case = service.analyze(
        complaint=domain_complaint,
        demo_mode=bool(getattr(complaint, "demo_mode", False)),
    )

    # 4. Serialize to PredictionOut
    return service.to_prediction_out(case)
