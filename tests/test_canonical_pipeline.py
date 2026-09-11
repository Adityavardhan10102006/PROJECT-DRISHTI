"""
tests/test_canonical_pipeline.py — Project DRISHTI
====================================================
Comprehensive automated test suite for the canonical demo case system (CASE-001-UPI-CRITICAL),
the real DRISHTI analysis pipeline execution, database persistence, timeline tracking,
and legacy alias resolution.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from backend.auth.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "admin", "role": "admin", "uid": 1})
    return {"Authorization": f"Bearer {token}"}


def test_canonical_cases_exist(client, auth_headers):
    """Verify that canonical demo cases exist in the case ledger."""
    res = client.get("/cases/", headers=auth_headers)
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) >= 5

    case_ids = [c["case_id"] for c in cases]
    assert "CASE-001-UPI-CRITICAL" in case_ids or "DR-2026-1001" in case_ids


def test_canonical_case_001_detail(client, auth_headers):
    """Verify dossier retrieval for CASE-001-UPI-CRITICAL."""
    res = client.get("/cases/CASE-001-UPI-CRITICAL", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "CASE-001" in data["case_id"] or "DR-2026-1001" in data["case_id"]
    assert data["amount"] == 85000.0
    assert data["fraud_type"] == "upi_fraud"


def test_real_pipeline_execution_and_persistence(client, auth_headers):
    """
    Verify clicking RUN DRISHTI ANALYSIS executes the real backend pipeline
    and persists updated predictions and timeline events to SQLite.
    """
    res = client.post("/cases/CASE-001-UPI-CRITICAL/analyze", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    # 1. Prediction values are real numbers (not fake strings or nulls)
    assert data["predicted_cashout_amount"] is not None
    assert float(data["predicted_cashout_amount"]) > 0
    assert data["predicted_time_peak_minutes"] is not None
    assert int(data["predicted_time_peak_minutes"]) > 0

    # 2. Money trail is reconstructed from transactions
    assert "money_trail" in data
    trail = data["money_trail"]
    assert "hops" in trail
    assert len(trail["hops"]) >= 1
    assert trail["hops"][0]["from_account"] is not None
    assert trail["hops"][0]["to_account"] is not None

    # 3. Top-K candidate ATMs
    assert "top_k_atms" in data
    assert len(data["top_k_atms"]) >= 1
    top1 = data["top_k_atms"][0]
    assert "atm_id" in top1
    assert "lat" in top1 and "lon" in top1
    assert -90.0 <= top1["lat"] <= 90.0
    assert -180.0 <= top1["lon"] <= 180.0

    # 4. 5D Intelligence Output
    assert "five_d" in data
    five_d = data["five_d"]
    assert "where" in five_d
    assert "when" in five_d
    assert "amount" in five_d
    assert "why" in five_d
    assert "action" in five_d

    # 5. Timeline reflects the analysis execution
    t_res = client.get("/cases/CASE-001-UPI-CRITICAL/timeline", headers=auth_headers)
    assert t_res.status_code == 200
    timeline = t_res.json()
    event_types = [e["event_type"] for e in timeline]
    assert "INTELLIGENCE_ANALYZED" in event_types or "COMPLAINT_ANALYZED" in event_types


def test_legacy_alias_resolution(client, auth_headers):
    """Verify that querying legacy DR-2026-1001 seamlessly resolves to CASE-001-UPI-CRITICAL."""
    res = client.get("/cases/DR-2026-1001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] in ("CASE-001-UPI-CRITICAL", "DR-2026-1001")


def test_invalid_case_id_returns_404(client, auth_headers):
    """Verify proper 404 handling for non-existent cases."""
    res = client.get("/cases/NON-EXISTENT-CASE-9999", headers=auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
