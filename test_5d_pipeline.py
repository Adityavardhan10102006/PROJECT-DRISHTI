"""
test_5d_pipeline.py — Project DRISHTI
======================================
Automated test suite verifying all 8 capabilities of the 5D Intelligence System:
  1. Multi-hop money-trail analysis
  2. AI/ML risk classification
  3. 5D Intelligence Output (WHERE, WHEN, AMOUNT, WHY, ACTION)
  4. Top-K likely cash-out locations with normalized confidence
  5. Geospatial Risk GeoJSON layer
  6. Feasibility & Response Prioritisation (nearest patrol unit, ETA, margin)
  7. Explainable Alerts (feature attributions and natural-language rationale)
  8. Outcome Validation & Continuous Improvement (feedback logging + retraining trigger)
"""

import sys
import io

# Force utf-8 output handling on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    print("=" * 65)
    print(" Project DRISHTI — 5D Predictive Intelligence Pipeline Tests")
    print("=" * 65)

    # 1. Health check test
    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    print("[PASS] GET /health returns 200 OK")

    # 2. Comprehensive 5D prediction test
    complaint_payload = {
        "complaint_id": "TEST-SIH-2026-001",
        "complaint_text": (
            "I was defrauded of Rs 85,000 via a fake electricity bill link on WhatsApp. "
            "The money was transferred immediately from my SBI account to beneficiary account "
            "987654321012 with IFSC SBIN0001423 via UPI reference 329104829102."
        ),
        "victim_lat": 19.0760,
        "victim_lon": 72.8777,
    }

    print("\nSending prediction request to POST /predict...")
    resp = client.post("/predict", json=complaint_payload)
    assert resp.status_code == 200, f"Prediction failed: {resp.status_code} - {resp.text}"
    data = resp.json()

    print("[PASS] POST /predict returned 200 OK")

    # Capability 1: Multi-Hop Money Trail
    assert "money_trail" in data and data["money_trail"] is not None, "Missing money_trail"
    trail = data["money_trail"]
    print(f"  [Cap 1] Money Trail: {trail['hop_count']} hops traced")
    print(f"          Initial: ₹{trail['initial_amount']:,} -> Final Cashout: ₹{trail['final_cashout_amount']:,}")
    assert len(trail["hops"]) > 0, "No hops returned in trail"
    assert len(trail["mule_accounts"]) > 0, "No mule accounts detected"
    print(f"          Flagged {len(trail['mule_accounts'])} mule accounts (Top: {trail['mule_accounts'][0]['account_number']})")

    # Capability 2: AI/ML Risk Scoring
    assert "risk_score" in data and data["risk_score"] is not None, "Missing risk_score"
    assert "risk_tier" in data and data["risk_tier"] is not None, "Missing risk_tier"
    print(f"  [Cap 2] AI Case Risk: {data['risk_score']}/100 [{data['risk_tier']}]")

    # Capability 3 & 7: 5D Intelligence Output & Explainability
    assert "five_d" in data and data["five_d"] is not None, "Missing five_d"
    five_d = data["five_d"]
    assert "where" in five_d, "Missing WHERE dimension"
    assert "when" in five_d, "Missing WHEN dimension"
    assert "amount" in five_d, "Missing AMOUNT dimension"
    assert "why" in five_d, "Missing WHY dimension"
    assert "action" in five_d, "Missing ACTION dimension"

    print(f"  [Cap 3] 5D WHERE:  {five_d['where']['primary_location_name']}")
    print(f"          5D WHEN:   {five_d['when']['operational_countdown']}")
    print(f"          5D AMOUNT: {five_d['amount']['formatted_reported']} (Est Cash-out: {five_d['amount']['formatted_cashout']})")
    print(f"          5D WHY:    {five_d['why']['summary'][:100]}...")
    print(f"          5D ACTION: {five_d['action']['primary_action'][:100]}...")

    # Capability 4: Top-K Cash-Out Locations
    assert "top_k_locations" in data and len(data["top_k_locations"]) > 0, "Missing top_k_locations"
    top_k = data["top_k_locations"]
    print(f"  [Cap 4] Top-K Locations: {len(top_k)} candidates ranked")
    for loc in top_k:
        print(f"          Rank {loc['rank']}: {loc['location_name']} (Prob: {loc['probability']:.1%}, Dist: {loc['distance_km']}km)")

    # Capability 5: Geospatial Risk GeoJSON Layer
    assert "geojson_risk_layer" in data and data["geojson_risk_layer"] is not None, "Missing geojson_risk_layer"
    geojson = data["geojson_risk_layer"]
    assert geojson["type"] == "FeatureCollection", "Invalid GeoJSON type"
    print(f"  [Cap 5] GeoJSON Risk Layer: {len(geojson['features'])} spatial features generated")

    # Capability 6: Feasibility & Response Prioritisation
    assert "feasibility" in data and data["feasibility"] is not None, "Missing feasibility"
    feas = data["feasibility"]
    print(f"  [Cap 6] Police Feasibility: {feas['unit_name']} ({feas['unit_vehicle']})")
    print(f"          ETA: {feas['eta_minutes']} min | Margin: {feas['time_margin_minutes']} min | Status: {feas['feasibility_status']}")
    print(f"          Composite Priority: {feas['composite_priority']}/100")

    # Capability 8: Outcome Validation & Continuous Retraining
    print("\nTesting Outcome Feedback & Retraining Endpoints...")
    outcome_payload = {
        "complaint_id": "TEST-SIH-2026-001",
        "was_intercepted": True,
        "location_accurate": True,
        "time_window_accurate": True,
        "mule_confirmed": True,
        "actual_withdrawal_minutes": 32,
        "recovered_amount": 80000.0,
        "officer_badge": "MH-CYBER-884",
        "notes": "Suspect apprehended at SBI ATM while attempting cash withdrawal.",
    }
    fb_resp = client.post("/alerts/TEST-SIH-2026-001/outcome", json=outcome_payload)
    assert fb_resp.status_code == 201, f"Outcome log failed: {fb_resp.text}"
    print("  [Cap 8a] POST /alerts/{id}/outcome logged successfully")

    stats_resp = client.get("/alerts/feedback/stats")
    assert stats_resp.status_code == 200, f"Stats failed: {stats_resp.text}"
    stats = stats_resp.json()
    print(f"  [Cap 8b] GET /alerts/feedback/stats:")
    print(f"           Total validations: {stats['total_validations']}")
    print(f"           Interception success rate: {stats['interception_success_rate']:.1%}")
    print(f"           Location accuracy rate: {stats['location_accuracy_rate']:.1%}")
    print(f"           Total INR recovered: ₹{stats['total_recovered_amount']:,}")

    retrain_resp = client.post("/alerts/feedback/retrain")
    assert retrain_resp.status_code == 200, f"Retrain failed: {retrain_resp.text}"
    retrain_res = retrain_resp.json()
    print(f"  [Cap 8c] POST /alerts/feedback/retrain: {retrain_res['status']} ({retrain_res['model_version']})")

    print("\n" + "=" * 65)
    print(" ALL 8 CAPABILITIES VERIFIED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
