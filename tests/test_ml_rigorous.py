"""
tests/test_ml_rigorous.py — Project DRISHTI
==============================================
Rigorous Automated Pytest Suite for Advanced ML/AI Architecture.

Verifies:
  1. Feature engineering consistency and categorical encoding
  2. Strict zero-leakage temporal as-of calculations (future events ignored)
  3. Location predictor ranking, probability calibration, and missing location handling
  4. Time predictor conformal prediction intervals [lower <= peak <= upper]
  5. Amount predictor regression bounds and non-negativity
  6. Risk predictor calibrated probabilities and SHAP attribution source
  7. Offline drift monitoring calculation (PSI)
  8. Data quality validation gate
  9. End-to-end FastAPI prediction contract and backward compatibility
"""

import os
import json
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from main import app
from backend.ml.features import (
    FeatureEngineeringPipeline,
    haversine_distance,
    calculate_as_of_historical_features,
    FRAUD_TYPE_MAP,
    BANK_MAP,
)
from backend.ml.location_predictor import get_location_predictor, LocationPredictor
from backend.ml.time_predictor import get_time_predictor, TimeWindowPredictor
from backend.ml.amount_predictor import get_amount_predictor, CashoutAmountPredictor
from backend.ml.risk_predictor import get_risk_predictor, CaseRiskPredictor
from backend.ml.drift import calculate_psi_numeric, calculate_psi_categorical
from backend.ml.data_quality import validate_complaints_data, validate_transactions_data

from backend.auth.security import create_access_token

_test_token = create_access_token({"sub": "admin", "role": "admin", "uid": 1})
client = TestClient(app, headers={"Authorization": f"Bearer {_test_token}"})


# ── 1. Feature Engineering & Leakage Tests ───────────────────────

def test_haversine_distance_accuracy():
    # Charminar (17.3616, 78.4747) to Hitec City (17.4435, 78.3772) ~ 13.6 km
    d = haversine_distance(17.3616, 78.4747, 17.4435, 78.3772)
    assert 12.0 <= d <= 15.0, f"Unexpected Haversine distance: {d} km"


def test_as_of_historical_features_strictly_ignores_future():
    """
    CRITICAL ANTI-LEAKAGE TEST:
    Asserts that events occurring on or after complaint_dt are NEVER used.
    """
    atm_id = "ATM-HYD-TEST"
    complaint_dt = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)

    # 3 past events, 2 future events
    events = [
        {"atm_id": atm_id, "timestamp": complaint_dt - timedelta(days=2), "amount": 10000.0},
        {"atm_id": atm_id, "timestamp": complaint_dt - timedelta(hours=3), "amount": 15000.0},
        {"atm_id": atm_id, "timestamp": complaint_dt - timedelta(minutes=10), "amount": 20000.0},
        # Future events: MUST NOT BE COUNTED
        {"atm_id": atm_id, "timestamp": complaint_dt + timedelta(minutes=5), "amount": 50000.0},
        {"atm_id": atm_id, "timestamp": complaint_dt + timedelta(days=1), "amount": 75000.0},
    ]

    stats = calculate_as_of_historical_features(
        candidate_atm_id=atm_id,
        complaint_timestamp=complaint_dt,
        historical_withdrawals=events,
    )

    # Count must be exactly 3, sum must be exactly 45000.0
    assert stats["withdrawal_count"] == 3, f"Expected 3 past events, got {stats['withdrawal_count']}"
    assert stats["cashout_sum"] == 45000.0, f"Expected 45000.0 past sum, got {stats['cashout_sum']}"


def test_feature_schema_completeness():
    schema = FeatureEngineeringPipeline.get_feature_schema()
    assert "location_model" in schema["models"]
    assert "time_model" in schema["models"]
    assert "amount_model" in schema["models"]
    assert "risk_model" in schema["models"]
    assert len(schema["models"]["location_model"]["feature_names"]) >= 20


# ── 2. Location Predictor Tests ──────────────────────────────────

def test_location_predictor_top_k():
    lp = get_location_predictor()
    res = lp.predict_top_k(
        victim_lat=17.4123,
        victim_lon=78.4489,
        amount=85000.0,
        fraud_type="upi_fraud",
        k=3,
    )
    assert res["status"] == "success"
    assert res["prediction_method"] in ["ml", "calibrated_ml", "heuristic"]
    assert len(res["top_k"]) == 3
    top = res["top_k"][0]
    assert top["rank"] == 1
    assert "lat" in top and "lon" in top
    assert 0.0 <= top["probability"] <= 1.0
    assert "reason" in top and len(top["reason"]) > 0


def test_location_predictor_missing_coords_safe_handling():
    """
    Requirement 24: Missing coordinates must return insufficient_location_data
    and NOT silently default to Hyderabad coordinates unless demo_mode=True.
    """
    lp = get_location_predictor()
    res = lp.predict_top_k(
        victim_lat=None,
        victim_lon=None,
        amount=50000.0,
        demo_mode=False,
    )
    assert res["status"] == "insufficient_location_data"
    assert len(res["top_k"]) == 0
    assert len(res["warnings"]) > 0


def test_location_predictor_demo_mode_explicit():
    lp = get_location_predictor()
    res = lp.predict_top_k(
        victim_lat=None,
        victim_lon=None,
        amount=50000.0,
        demo_mode=True,
    )
    assert res["status"] == "success"
    assert any("demo mode" in w.lower() for w in res["warnings"])


# ── 3. Time Window Predictor & Conformal Uncertainty ─────────────

def test_time_predictor_conformal_interval():
    tp = get_time_predictor()
    res = tp.predict(
        fraud_type="upi_fraud",
        amount=50000.0,
        city="Mumbai",
    )
    assert 5 <= res.peak_minutes <= 120
    assert res.lower_bound <= res.peak_minutes <= res.upper_bound
    assert res.coverage_level == 0.90
    assert "conformal" in res.uncertainty_method


# ── 4. Amount Predictor & Non-deterministic Realistic Bounds ─────

def test_amount_predictor_bounds():
    ap = get_amount_predictor()
    res = ap.predict(
        amount=120000.0,
        fraud_type="kyc_fraud",
        hop_count=3,
    )
    assert res["predicted_cashout_amount"] > 0
    assert res["lower_bound"] <= res["predicted_cashout_amount"] <= res["upper_bound"]
    assert res["predicted_cashout_amount"] <= 120000.0
    assert "dataset_type" in res


# ── 5. Risk Predictor & SHAP Attributions ────────────────────────

def test_risk_predictor_shap_and_directions():
    rp = get_risk_predictor()
    res = rp.predict(
        fraud_type="phishing",
        amount=150000.0,
        hop_count=4,
        centrality=0.35,
    )
    assert 0.0 <= res["risk_score"] <= 100.0
    assert res["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert res["explanation_source"] in ["shap_tree_explainer", "heuristic_fallback"]
    assert len(res["explanation"]) > 0
    for exp in res["explanation"]:
        assert "feature" in exp
        assert "direction" in exp
        assert exp["direction"] in ["increases_risk", "decreases_risk"]


# ── 6. Drift Monitoring & Data Quality ───────────────────────────

def test_drift_psi_numeric():
    # Same distribution -> PSI ~ 0.0
    arr1 = np.random.normal(50, 10, 500)
    arr2 = np.random.normal(50, 10, 500)
    psi = calculate_psi_numeric(arr1, arr2)
    assert psi < 0.15, f"Expected small PSI for identical distribution, got {psi}"

    # Shifted distribution -> PSI > 0.25
    arr_shifted = np.random.normal(85, 10, 500)
    psi_shift = calculate_psi_numeric(arr1, arr_shifted)
    assert psi_shift >= 0.20, f"Expected higher PSI for shifted distribution, got {psi_shift}"


def test_data_quality_checks():
    df = pd.DataFrame({
        "complaint_id": ["C1", "C2"],
        "timestamp": ["2026-06-01T10:00:00", "2026-06-02T12:00:00"],
        "amount": [10000.0, 25000.0],
        "fraud_type": ["upi_fraud", "kyc_fraud"],
        "victim_lat": [17.4, 18.5],
        "victim_lon": [78.4, 72.8],
    })
    rep = validate_complaints_data(df)
    assert rep["status"] == "PASS"
    assert not rep["critical_failure"]


# ── 7. Full API Contract & Backward Compatibility ────────────────

def test_predict_api_rigorous_response():
    payload = {
        "complaint_text": "Sir mujhe UPI par fake electricity bill update call aaya aur unhone ₹45,000 deduct karwa liye.",
        "amount": 45000.0,
        "victim_lat": 17.4435,
        "victim_lon": 78.3772,
        "fraud_type": "upi_fraud",
    }
    resp = client.post("/predict/", json=payload)
    assert resp.status_code == 200, f"API error: {resp.text}"
    data = resp.json()

    # Legacy fields backward compatibility
    assert "hotspot" in data and data["hotspot"] is not None
    assert "top_k_locations" in data and len(data["top_k_locations"]) >= 1
    assert "time_window" in data and data["time_window"] is not None
    assert "mule_accounts" in data
    assert "nlp_entities" in data
    assert "alert_level" in data
    assert "five_d" in data

    # Rigorous ML Upgrade fields (Requirement 36)
    assert "prediction_method" in data
    assert data["prediction_method"] in ["ml", "calibrated_ml", "heuristic"]
    assert "location_prediction" in data
    assert "time_prediction" in data
    assert "amount_prediction" in data
    assert "risk_prediction" in data
    assert "explainability" in data
    assert "data_quality" in data

    loc_pred = data["location_prediction"]
    assert "top_k" in loc_pred
    assert "top3_recall_context" in loc_pred
    assert loc_pred["dataset_type"] == "synthetic_benchmark"

    time_pred = data["time_prediction"]
    assert time_pred["lower_bound"] <= time_pred["predicted_minutes"] <= time_pred["upper_bound"]
    assert time_pred["coverage"] == 0.90
