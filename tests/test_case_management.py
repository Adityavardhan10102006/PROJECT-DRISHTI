"""
tests/test_case_management.py — Project DRISHTI
===============================================
Comprehensive tests for Case Management, Timeline Events,
Field Outcome Reporting, and Candidate Retraining Pipeline.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from backend.database import SessionLocal, Case, CaseEvent, AuditLog, init_demo_cases
from backend.services.case_service import CaseService, get_case_service
from backend.domain.case_management import (
    CaseStatus,
    compute_priority,
    calculate_prediction_accuracy,
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post(
        "/auth/login",
        json={"username": "admin", "password": "Drishti@2026"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def admin_headers(auth_headers):
    return auth_headers


@pytest.fixture(scope="module")
def analyst_headers(client):
    res = client.post(
        "/auth/login",
        json={"username": "analyst", "password": "Analyst@2026"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def investigator_headers(client):
    res = client.post(
        "/auth/login",
        json={"username": "investigator", "password": "Investigate@2026"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# 1. UNIT TESTS: ACCURACY & PRIORITY FORMULA
# ─────────────────────────────────────────────

def test_priority_formula_consistency():
    """Verify standardized formula: 0.60 * Risk + 0.40 * Feasibility."""
    assert compute_priority(100.0, 100.0) == 100.0
    assert compute_priority(0.0, 0.0) == 0.0
    assert compute_priority(80.0, 90.0) == round(0.60 * 80.0 + 0.40 * 90.0, 2)
    assert compute_priority(94.0, 93.5) == round(0.60 * 94.0 + 0.40 * 93.5, 2)


def test_calculate_prediction_accuracy():
    """Verify accurate computation of prediction accuracy metrics."""
    case_mock = {
        "case_id": "TEST-01",
        "predicted_cashout_amount": 42000.0,
        "predicted_time_earliest_minutes": 20,
        "predicted_time_latest_minutes": 55,
        "incident_time": "2026-09-09T10:00:00+00:00",
        "top_k_atms": [
            {"rank": 1, "atm_id": "ATM-HYD-047"},
            {"rank": 2, "atm_id": "ATM-HYD-012"},
        ],
    }

    # Scenario A: Exact Top-1 hit within window
    outcome_hit = {
        "actual_atm_id": "ATM-HYD-047",
        "actual_amount": 40500.0,
        "actual_time": "2026-09-09T10:35:00+00:00",  # 35 min elapsed (within 20-55)
        "was_intercepted": True,
        "is_correct": True,
    }
    metrics = calculate_prediction_accuracy(case_mock, outcome_hit)
    assert metrics["location_accuracy"] is True
    assert metrics["top_k_hit"] is True
    assert metrics["time_window_accuracy"] is True
    assert metrics["amount_error"] == 1500.0
    assert metrics["overall_success"] is True

    # Scenario B: Top-K hit (rank 2) but outside time window
    outcome_partial = {
        "actual_atm_id": "ATM-HYD-012",
        "actual_amount": 42000.0,
        "actual_time": "2026-09-09T11:30:00+00:00",  # 90 min elapsed (outside 20-55)
        "was_intercepted": False,
        "is_correct": False,
    }
    metrics2 = calculate_prediction_accuracy(case_mock, outcome_partial)
    assert metrics2["location_accuracy"] is False
    assert metrics2["top_k_hit"] is True
    assert metrics2["time_window_accuracy"] is False
    assert metrics2["amount_error"] == 0.0
    assert metrics2["overall_success"] is False


# ─────────────────────────────────────────────
# 2. INTEGRATION TESTS: CASE REPOSITORY & STATS
# ─────────────────────────────────────────────

def test_seeded_demo_cases_exist(client, auth_headers):
    """Ensure the 5 deterministic demo cases are loaded."""
    res = client.get("/cases/", headers=auth_headers)
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) >= 5
    case_ids = [c["case_id"] for c in cases]
    assert "DR-2026-1001" in case_ids
    assert "DR-2026-1002" in case_ids
    assert "DR-2026-1003" in case_ids
    assert "DR-2026-1004" in case_ids
    assert "DR-2026-1005" in case_ids


def test_command_center_stats(client, auth_headers):
    """Verify Command Center dynamic KPI metrics endpoint."""
    res = client.get("/cases/stats", headers=auth_headers)
    assert res.status_code == 200
    stats = res.json()
    assert "total_cases" in stats
    assert stats["total_cases"] >= 5
    assert "critical_cases" in stats
    assert "active_cases" in stats
    assert "successful_predictions" in stats
    assert "prediction_accuracy_pct" in stats


def test_case_detail_endpoint(client, auth_headers):
    """Verify retrieval of complete case dossier."""
    res = client.get("/cases/DR-2026-1001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "DR-2026-1001"
    assert data["risk_level"] == "CRITICAL"
    assert "money_trail" in data
    assert "top_k_atms" in data
    assert "five_d" in data
    assert "police_feasibility" in data


def test_case_timeline_endpoint(client, auth_headers):
    """Verify chronological timeline retrieval."""
    res = client.get("/cases/DR-2026-1001/timeline", headers=auth_headers)
    assert res.status_code == 200
    timeline = res.json()
    assert len(timeline) >= 6
    types = [t["event_type"] for t in timeline]
    assert "COMPLAINT_RECEIVED" in types
    assert "COMPLAINT_ANALYZED" in types
    assert "RISK_PREDICTED" in types
    assert "CASHOUT_LOCATION_PREDICTED" in types


def test_case_status_update_and_timeline(client, investigator_headers):
    """Verify updating status updates the dossier and adds a timeline event."""
    res = client.patch(
        "/cases/DR-2026-1001/status",
        headers=investigator_headers,
        json={"status": "FIELD_ACTION", "note": "Patrol dispatched to SBI Banjara Hills"},
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["status"] == "FIELD_ACTION"

    # Verify timeline reflects the transition
    t_res = client.get("/cases/DR-2026-1001/timeline", headers=investigator_headers)
    assert t_res.status_code == 200
    t_events = t_res.json()
    last_event = t_events[-1]
    assert last_event["event_type"] == "STATUS_CHANGED"
    assert "FIELD_ACTION" in last_event["description"]


def test_assign_investigator_rbac(client, investigator_headers, admin_headers):
    """Only admin or analyst can assign cases."""
    # Investigator attempt -> 403 Forbidden
    res_inv = client.patch(
        "/cases/DR-2026-1003/assign",
        headers=investigator_headers,
        json={"investigator": "Insp. Vikram Kumar"},
    )
    assert res_inv.status_code == 403

    # Admin attempt -> 200 OK
    res_admin = client.patch(
        "/cases/DR-2026-1003/assign",
        headers=admin_headers,
        json={"investigator": "Insp. Vikram Kumar"},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["assigned_investigator"] == "Insp. Vikram Kumar"


def test_record_outcome_and_accuracy_evaluation(client, investigator_headers):
    """Test field outcome reporting and automated prediction accuracy calculation."""
    payload = {
        "actual_atm_id": "ATM-HYD-047",
        "actual_time": datetime.now(timezone.utc).isoformat(),
        "actual_amount": 81000.0,
        "was_intercepted": True,
        "is_correct": True,
        "notes": "Suspect apprehended at kiosk with withdrawal card.",
    }
    res = client.post(
        "/cases/DR-2026-1001/outcome",
        headers=investigator_headers,
        json=payload,
    )
    assert res.status_code == 200
    case_out = res.json()
    assert case_out["status"] == "RESOLVED"
    assert case_out["outcome"] is not None
    assert case_out["outcome_metrics"] is not None
    metrics = case_out["outcome_metrics"]
    assert metrics["location_accuracy"] is True
    assert metrics["top_k_hit"] is True
    assert "amount_error" in metrics


def test_candidate_model_retraining_gate(client, investigator_headers, admin_headers):
    """Verify RBAC and candidate promotion evaluation pipeline."""
    # Investigator -> 403 Forbidden
    res_inv = client.post("/cases/candidate-retrain", headers=investigator_headers)
    assert res_inv.status_code == 403

    # Admin -> 200 OK
    res_admin = client.post("/cases/candidate-retrain", headers=admin_headers)
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "status" in data
    assert "production_model_version" in data
