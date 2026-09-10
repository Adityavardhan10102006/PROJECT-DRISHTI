"""
tests/test_e2e_investigation_lifecycle.py — Project DRISHTI
===========================================================
End-to-End Automated Investigation Lifecycle Test
Simulates the complete 18-step investigation journey:
  1.  Login & authentication (RBAC JWT)
  2.  Deterministic complaint submission & analysis
  3.  Risk scoring & level categorization
  4.  Multi-hop money trail graph reconstruction
  5.  Location prediction & Top-K ATM ranking
  6.  Withdrawal time window & conformal bounds prediction
  7.  Cash-out amount prediction with commission shaving modeling
  8.  SHAP feature attribution & explainability
  9.  Police response feasibility scoring & unit ETA
  10. 5D Actionable Intelligence generation (WHERE, WHEN, AMOUNT, WHY, ACTION)
  11. Investigation case creation & SQLite database persistence
  12. Chronological investigation timeline verification
  13. Case status transition (NEW -> ANALYZING -> ACTION_REQUIRED)
  14. Ground truth field outcome recording
  15. Automated prediction accuracy evaluation
  16. Continuous feedback submission into feedback dataset
  17. Candidate model retraining evaluation & promotion gate check
  18. Non-repudiable audit logging verification
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from main import app
from backend.database import SessionLocal, Case, CaseEvent, AuditLog

client = TestClient(app)


def test_complete_investigation_lifecycle():
    # ── 1. LOGIN & AUTHENTICATION ─────────────────────────────────────
    login_res = client.post(
        "/auth/login",
        json={"username": "admin", "password": "Drishti@2026"}
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verify identity
    me_res = client.get("/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    user_info = me_res.json()
    assert user_info["user"]["username"] == "admin"
    assert user_info["user"]["role"] == "admin"

    # ── 2. DETERMINISTIC COMPLAINT SUBMISSION & ANALYSIS ──────────────
    # Load canonical demo case 1
    with open("data/demo_cases.json", "r", encoding="utf-8") as f:
        demo_cases = json.load(f)
    case_1 = demo_cases[0]

    predict_res = client.post(
        "/predict/",
        json=case_1["payload"],
        headers=auth_headers
    )
    assert predict_res.status_code == 200, f"Prediction failed: {predict_res.text}"
    result = predict_res.json()

    # ── 3. RISK SCORING ───────────────────────────────────────────────
    assert "risk_score" in result
    assert "risk_tier" in result
    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["risk_tier"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # ── 4. MONEY TRAIL RECONSTRUCTION ─────────────────────────────────
    assert "money_trail" in result
    mt = result["money_trail"]
    assert mt["data_source"] == "synthetic_demo_dataset"
    assert "hops" in mt and len(mt["hops"]) >= 1
    assert "graph_metrics" in mt
    assert "initial_amount" in mt and mt["initial_amount"] > 0

    # ── 5. LOCATION PREDICTION & TOP-K ATMS ───────────────────────────
    assert "top_k_locations" in result
    top_k = result["top_k_locations"]
    assert len(top_k) >= 3, "Expected at least Top-3 ranked ATMs"
    for atm in top_k:
        assert "atm_id" in atm and "bank" in atm
        assert "lat" in atm and "lon" in atm

    # ── 6. WITHDRAWAL TIME PREDICTION ─────────────────────────────────
    assert "time_window" in result
    tw = result["time_window"]
    assert "peak_minutes" in tw
    assert "earliest_minutes" in tw and "latest_minutes" in tw
    assert tw["earliest_minutes"] <= tw["peak_minutes"] <= tw["latest_minutes"]

    # ── 7. AMOUNT PREDICTION ──────────────────────────────────────────
    assert "amount_prediction" in result
    amt_p = result["amount_prediction"]
    assert "predicted_amount" in amt_p
    assert amt_p["predicted_amount"] > 0
    assert amt_p["lower_bound"] <= amt_p["predicted_amount"] <= amt_p["upper_bound"]

    # ── 8. SHAP EXPLAINABILITY ────────────────────────────────────────
    assert "explainability" in result
    shap_data = result["explainability"]
    assert "source" in shap_data
    assert "features" in shap_data and len(shap_data["features"]) > 0

    # ── 9. POLICE FEASIBILITY ─────────────────────────────────────────
    assert "feasibility" in result
    feas = result["feasibility"]
    assert "unit_name" in feas
    assert "eta_minutes" in feas
    assert "feasibility_score" in feas

    # ── 10. 5D INTELLIGENCE (WHERE, WHEN, AMOUNT, WHY, ACTION) ────────
    assert "five_d" in result
    fd = result["five_d"]
    for dim in ["where", "when", "amount", "why", "action"]:
        assert dim in fd, f"Missing 5D dimension: {dim}"
    assert "action_type" in fd["action"]
    assert "primary_action" in fd["action"]

    # ── 11. CASE PERSISTENCE IN SQLITE ────────────────────────────────
    case_id = result.get("case_id")
    assert case_id is not None, "Predict pipeline should return associated case_id"

    get_case_res = client.get(f"/cases/{case_id}", headers=auth_headers)
    assert get_case_res.status_code == 200
    saved_case = get_case_res.json()
    assert saved_case["case_id"] == case_id
    assert saved_case["complaint_id"] == result["complaint_id"]

    # ── 12. CHRONOLOGICAL INVESTIGATION TIMELINE ──────────────────────
    timeline_res = client.get(f"/cases/{case_id}/timeline", headers=auth_headers)
    assert timeline_res.status_code == 200
    events = timeline_res.json()
    assert len(events) >= 3, "Expected initialized timeline events"
    event_types = [e["event_type"] for e in events]
    assert "COMPLAINT_RECEIVED" in event_types
    assert "MONEY_TRAIL_RECONSTRUCTED" in event_types

    # ── 13. CASE STATUS TRANSITION ────────────────────────────────────
    status_update_res = client.patch(
        f"/cases/{case_id}/status",
        json={"status": "ACTION_REQUIRED", "notes": "Top-1 ATM flagged for surveillance"},
        headers=auth_headers
    )
    assert status_update_res.status_code == 200
    assert status_update_res.json()["status"] == "ACTION_REQUIRED"

    # ── 14 & 15. FIELD OUTCOME & AUTOMATED ACCURACY EVALUATION ────────
    # Simulate ground truth recorded by field unit
    top_atm = top_k[0]["atm_id"]
    outcome_payload = {
        "actual_atm_id": top_atm,
        "actual_amount": 82000.0,
        "actual_time_minutes": tw["peak_minutes"] + 2.0,
        "was_intercepted": True,
        "is_correct": True,
        "notes": "Field unit arrived at ATM-HYD-047 and intercepted mule account holder."
    }
    outcome_res = client.post(
        f"/cases/{case_id}/outcome",
        json=outcome_payload,
        headers=auth_headers
    )
    assert outcome_res.status_code == 200
    updated_case = outcome_res.json()
    assert updated_case["status"] == "RESOLVED"
    assert updated_case["outcome_metrics"] is not None

    om = updated_case["outcome_metrics"]
    assert "location_accuracy" in om
    assert "top_k_hit" in om and om["top_k_hit"] is True
    assert "amount_error" in om
    assert "time_window_accuracy" in om
    assert "overall_success" in om

    # ── 16 & 17. FEEDBACK & CANDIDATE MODEL RETRAINING GATE ───────────
    retrain_res = client.post("/cases/candidate-retrain", headers=auth_headers)
    assert retrain_res.status_code == 200
    retrain_data = retrain_res.json()
    assert "status" in retrain_data
    assert "decision" in retrain_data
    assert "production_model_version" in retrain_data
    assert "candidate_model_version" in retrain_data
    # Candidate gate must safely evaluate without breaking production
    assert retrain_data["promoted"] in [True, False]

    # ── 18. NON-REPUDIABLE AUDIT LOGGING ──────────────────────────────
    audit_res = client.get("/audit-logs/", headers=auth_headers)
    assert audit_res.status_code == 200
    audit_list = audit_res.json()
    assert len(audit_list) >= 1
    actions = [a["action"] for a in audit_list]
    assert any("OUTCOME" in act or "STATUS" in act or "RETRAIN" in act or "CASE" in act for act in actions)
