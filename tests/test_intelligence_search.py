"""
tests/test_intelligence_search.py — Project DRISHTI
===================================================
Automated verification for Universal Intelligence Search,
Multi-Factor Cash-Out Prospects Ranking, and Data Integration Adapters.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    login_res = client.post(
        "/auth/login",
        json={"username": "admin", "password": "Drishti@2026"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_search_requires_authentication():
    res = client.get("/search?q=test")
    assert res.status_code in [401, 403]


def test_intelligence_search_general(auth_headers):
    res = client.get("/intelligence/search?q=UPI&limit=20", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "total_matches" in data
    assert data["total_matches"] >= 0

    if data["results"]:
        first = data["results"][0]
        assert "entity_type" in first
        assert "entity_id" in first
        assert "relevance_score" in first
        assert "relationship_summary" in first
        assert "matched_fields" in first
        # Verify descending order of relevance
        scores = [r["relevance_score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True)


def test_search_case_id(auth_headers):
    res = client.get("/search?q=CASE-001&entity_type=cases", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) >= 1
    top_result = data["results"][0]
    assert top_result["entity_type"] == "case"
    assert "CASE-001" in top_result["entity_id"]
    assert top_result["relevance_score"] > 0.5
    assert len(top_result["matched_fields"]) > 0


def test_search_atm_entities(auth_headers):
    res = client.get("/search?q=ATM&entity_type=atms&limit=10", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) >= 1
    assert data["results"][0]["entity_type"] == "atm"
    assert "Hyderabad" in data["results"][0]["location"]


def test_candidate_cashout_prospects(auth_headers):
    res = client.get(
        "/atms/candidates?victim_lat=17.4435&victim_lon=78.3772&amount=75000&fraud_type=upi_fraud&k=5",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "candidates" in data
    assert len(data["candidates"]) <= 5
    assert "scoring_formula" in data
    assert "decision_support_notice" in data

    if data["candidates"]:
        cand = data["candidates"][0]
        assert "atm_id" in cand
        assert "candidate_priority_score" in cand
        assert "why_factors" in cand
        assert len(cand["why_factors"]) >= 3
        assert "nearest_police_unit" in cand
        assert "time_match" in cand
        assert "amount_compatibility" in cand


def test_integration_sources_honest_status(auth_headers):
    res = client.get("/integration/sources", headers=auth_headers)
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 4

    # Ensure prototype sources are marked as AVAILABLE / ACTIVE
    proto_sources = [s for s in sources if not s.get("auth_required")]
    assert len(proto_sources) >= 4
    for p in proto_sources:
        assert p["status"] == "AVAILABLE"
        assert p["is_live"] is False  # Never falsely claimed as live
        assert "disclaimer" in p

    # Ensure institutional adapters are clearly marked as INTEGRATION READY or AWAITING AUTH
    inst_sources = [s for s in sources if s.get("auth_required")]
    assert len(inst_sources) >= 3
    for inst in inst_sources:
        assert inst["status"] in ["INTEGRATION_READY", "AWAITING_AUTHORIZED_FEED"]
        assert inst["is_live"] is False


def test_integration_provenance(auth_headers):
    res = client.get("/integration/provenance", headers=auth_headers)
    assert res.status_code == 200
    prov = res.json()
    assert prov["status"] == "success"
    assert prov["is_production_live"] is False
    assert "Synthetic Demonstration" in prov["badge"]
    assert prov["random_seed"] == 42
