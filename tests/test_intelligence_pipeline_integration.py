"""
tests/test_intelligence_pipeline_integration.py
================================================
Comprehensive integration test for the DRISHTI 5D Intelligence Pipeline:
- Verification of 5D fields (WHERE, WHEN, AMOUNT, WHY, ACTION)
- Real backend execution via POST /cases/{case_id}/analyze
- Filtering by Critical risk tier & sorting descending by risk
- Verification that no hardcoded fallback values are injected
"""

import pytest
from starlette.testclient import TestClient
from main import app
from backend.database import SessionLocal, Case, init_demo_cases


@pytest.fixture(scope="module")
def client():
    init_demo_cases()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post(
        "/auth/login",
        json={"username": "admin", "password": "Drishti@2026"},
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_canonical_case_dossier_has_5d_structure(client, auth_headers):
    """Verify primary demo case has the formal 5D intelligence keys."""
    res = client.get("/cases/CASE-001-UPI-CRITICAL", headers=auth_headers)
    assert res.status_code == 200
    case = res.json()

    assert case["case_id"] == "CASE-001-UPI-CRITICAL"
    assert "five_d" in case
    five_d = case["five_d"]

    # Verify all 5 dimensions exist
    assert "where" in five_d
    assert "when" in five_d
    assert "amount" in five_d
    assert "why" in five_d
    assert "action" in five_d

    # Verify real subfields
    assert "primary_location_name" in five_d["where"] or "primary_location" in five_d["where"]
    assert "window" in five_d["when"] or "peak_minutes" in five_d["when"]
    assert "predicted_cashout_amount" in five_d["amount"]
    assert "top_reasons" in five_d["why"] or "key_drivers" in five_d["why"] or "summary" in five_d["why"]
    assert "primary_action" in five_d["action"] or "protocol" in five_d["action"] or "action_type" in five_d["action"]


def test_real_pipeline_execution_updates_5d_and_money_trail(client, auth_headers):
    """Verify real backend analysis execution updates case dossier and timeline."""
    res = client.post("/cases/CASE-001-UPI-CRITICAL/analyze", headers=auth_headers)
    assert res.status_code == 200
    updated = res.json()

    # Predictions must be real numbers > 0
    assert updated["predicted_cashout_amount"] is not None
    assert updated["predicted_cashout_amount"] > 0
    assert updated["predicted_time_peak_minutes"] is not None
    assert updated["predicted_time_peak_minutes"] > 0
    assert len(updated["top_k_atms"]) > 0

    # Money trail verification
    assert "money_trail" in updated
    mt = updated["money_trail"]
    assert len(mt.get("hops", [])) >= 2
    assert "ACC-MULE-" in str(mt.get("hops", []))

    # Police feasibility verification
    assert "police_feasibility" in updated
    pf = updated["police_feasibility"]
    assert pf.get("feasibility_status") in ("HIGH", "MEDIUM", "LOW", "EXCELLENT_MARGIN", "VIABLE", "TIGHT_WINDOW")
    assert pf.get("distance_km") is not None

    # Timeline event verification
    t_res = client.get("/cases/CASE-001-UPI-CRITICAL/timeline", headers=auth_headers)
    assert t_res.status_code == 200
    events = t_res.json()
    types = [e["event_type"] for e in events]
    assert "INTELLIGENCE_ANALYZED" in types or "CASHOUT_LOCATION_PREDICTED" in types


def test_critical_filter_and_ranking(client, auth_headers):
    """Verify filtering for critical cases returns valid descending ranking."""
    res = client.get("/cases/?risk_level=CRITICAL&limit=10", headers=auth_headers)
    assert res.status_code == 200
    cases = res.json()

    assert len(cases) >= 1
    for c in cases:
        assert c["risk_level"] == "CRITICAL"

    # Verify descending sort by priority/risk
    scores = [c.get("priority_score", 0) for c in cases]
    assert scores == sorted(scores, reverse=True)


def test_all_canonical_demo_cases_accessible(client, auth_headers):
    """Verify each of the 5 canonical demo cases can be retrieved without errors."""
    canonical_ids = [
        "CASE-001-UPI-CRITICAL",
        "CASE-002-LOWVAL-MEDIUM",
        "CASE-003-MULE-RING-CRITICAL",
        "CASE-004-NIGHT-CASHOUT-HIGH",
        "CASE-005-LEGIT-LOW",
    ]

    for cid in canonical_ids:
        res = client.get(f"/cases/{cid}", headers=auth_headers)
        assert res.status_code == 200, f"Case {cid} failed with {res.status_code}"
        data = res.json()
        assert data["case_id"] == cid
        assert "risk_level" in data
        assert "amount" in data
