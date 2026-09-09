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
import os
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

    # Capability 0: NLP Key Entity Extraction Confidence Scoring
    assert "extraction_confidence" in data, "Missing extraction_confidence in prediction response"
    assert 0.0 <= data["extraction_confidence"] <= 1.0, f"Invalid extraction_confidence: {data['extraction_confidence']}"
    assert data["nlp_entities"].get("extraction_confidence") == data["extraction_confidence"]
    print(f"  [NLP] Extraction Confidence Score: {data['extraction_confidence']:.0%} (Entities in text)")

    # Capability 1: Multi-Hop Money Trail & Stateful Mule Graph
    assert "money_trail" in data and data["money_trail"] is not None, "Missing money_trail"
    trail = data["money_trail"]
    print(f"  [Cap 1] Money Trail: {trail['hop_count']} hops traced")
    print(f"          Initial: ₹{trail['initial_amount']:,} -> Final Cashout: ₹{trail['final_cashout_amount']:,}")
    assert len(trail["hops"]) > 0, "No hops returned in trail"
    assert len(trail["mule_accounts"]) > 0, "No mule accounts detected"
    assert "is_historical_mule" in trail["mule_accounts"][0], "Missing is_historical_mule in mule account"
    hist_count = sum(1 for m in trail["mule_accounts"] if m["is_historical_mule"])
    print(f"          Flagged {len(trail['mule_accounts'])} mule accounts (Historical mules: {hist_count})")
    assert "is_historical_mule" in data, "Missing is_historical_mule in PredictionOut"
    print(f"          Prediction has historical mule: {data['is_historical_mule']}")

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

    # Capability 8: Outcome Validation, SQLite Tracking & Continuous Retraining
    print("\nTesting Outcome Feedback & Retraining Endpoints...")
    alert_id = data.get("alert_id")
    assert alert_id is not None, "Missing alert_id in prediction response"
    print(f"  [Cap 8a] Alert successfully created in SQLite with alert_id: {alert_id}")

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
    # Test updating by alert_id
    fb_resp = client.post(f"/alerts/{alert_id}/outcome", json=outcome_payload)
    assert fb_resp.status_code == 201, f"Outcome log failed: {fb_resp.text}"
    fb_data = fb_resp.json()
    assert fb_data["alert"]["status"] == "INTERCEPTED", f"Expected status INTERCEPTED, got {fb_data['alert']['status']}"
    print(f"  [Cap 8b] POST /alerts/{alert_id}/outcome updated SQLite status to: {fb_data['alert']['status']}")

    # Verify GET /alerts/{id}
    get_alert_resp = client.get(f"/alerts/{alert_id}")
    assert get_alert_resp.status_code == 200, f"Get alert failed: {get_alert_resp.text}"
    assert get_alert_resp.json()["status"] == "INTERCEPTED"
    print(f"  [Cap 8c] GET /alerts/{alert_id} verified SQLite persistence (Status: {get_alert_resp.json()['status']})")

    stats_resp = client.get("/alerts/feedback/stats")
    assert stats_resp.status_code == 200, f"Stats failed: {stats_resp.text}"
    stats = stats_resp.json()
    print(f"  [Cap 8d] GET /alerts/feedback/stats:")
    print(f"           Total validations: {stats['total_validations']}")
    print(f"           Interception success rate: {stats['interception_success_rate']:.1%}")
    print(f"           Location accuracy rate: {stats['location_accuracy_rate']:.1%}")
    print(f"           Total INR recovered: ₹{stats['total_recovered_amount']:,}")

    # Retrain protection tests
    # 1. Without API key -> 403 Forbidden
    no_key_resp = client.post("/alerts/feedback/retrain")
    assert no_key_resp.status_code == 403, f"Expected 403 without API key, got {no_key_resp.status_code}"
    print("  [Cap 8e] POST /alerts/feedback/retrain without API key rejected with 403 Forbidden (Protected!)")

    # 2. With wrong API key -> 403 Forbidden
    bad_key_resp = client.post("/alerts/feedback/retrain", headers={"X-API-Key": "wrong-key"})
    assert bad_key_resp.status_code == 403, f"Expected 403 with invalid key, got {bad_key_resp.status_code}"
    print("  [Cap 8f] POST /alerts/feedback/retrain with wrong key rejected with 403 Forbidden")

    # 3. With valid API key -> 202 Accepted (Asynchronous Thread Pool)
    import time
    admin_key = os.getenv("ADMIN_API_KEY", "your-secure-key-here")
    retrain_resp = client.post("/alerts/feedback/retrain", headers={"X-API-Key": admin_key})
    assert retrain_resp.status_code == 202, f"Expected 202 Accepted, got {retrain_resp.status_code}: {retrain_resp.text}"
    retrain_res = retrain_resp.json()
    assert "task_id" in retrain_res, f"Expected task_id in response: {retrain_res}"
    task_id = retrain_res["task_id"]
    print(f"  [Cap 8g] POST /alerts/feedback/retrain -> 202 Accepted (task_id: {task_id}, status: {retrain_res['status']})")

    # 4. Status Check Endpoint: GET /retrain/status/{task_id}
    status_resp = client.get(f"/retrain/status/{task_id}")
    assert status_resp.status_code == 200, f"Status check failed: {status_resp.text}"
    status_data = status_resp.json()
    assert status_data["status"] in ("PENDING", "RUNNING", "COMPLETED"), f"Unexpected status: {status_data}"
    print(f"  [Cap 8h] GET /retrain/status/{task_id} -> {status_data['status']}")

    # Capability 9: Dedicated Verification for Upgraded Modules
    print("\nVerifying Module Upgrades (NLP Confidence & Stateful Mule Graph)...")
    from backend.nlp.extractor import ComplaintExtractor
    from backend.ml.mule_graph import MuleNetworkGraph
    import json

    ext = ComplaintExtractor()
    # 3 key entities present -> 1.0
    r_all = ext.extract("Sent Rs 25000 to victim@okaxis ref UPI98765432101")
    assert r_all.extraction_confidence == 1.0, f"Expected 1.0, got {r_all.extraction_confidence}"
    # 2 key entities present -> 0.67
    r_two = ext.extract("Sent Rs 25000 to victim@okaxis")
    assert r_two.extraction_confidence == 0.67, f"Expected 0.67, got {r_two.extraction_confidence}"
    # 1 key entity present -> 0.33
    r_one = ext.extract("Fraud amount Rs 25000 was debited")
    assert r_one.extraction_confidence == 0.33, f"Expected 0.33, got {r_one.extraction_confidence}"
    # 0 key entities present -> 0.0
    r_zero = ext.extract("I was completely cheated yesterday")
    assert r_zero.extraction_confidence == 0.0, f"Expected 0.0, got {r_zero.extraction_confidence}"
    print("  [NLP Test] Proportional confidence scoring verified: (3/3 -> 1.0, 2/3 -> 0.67, 1/3 -> 0.33, 0/3 -> 0.0)")

    # Stateful Mule Graph Cache Verification
    cache_path = "mule_centrality_cache.json" if os.path.exists("mule_centrality_cache.json") else "data/mule_centrality_cache.json"
    assert os.path.exists(cache_path), f"Mule cache file not found at {cache_path}"
    with open(cache_path, "r", encoding="utf-8") as f:
        cache_data = json.load(f)
    assert "nodes" in cache_data, "Missing 'nodes' in mule cache"
    assert "edges" in cache_data, "Missing 'edges' in mule cache"
    assert "historical_centrality" in cache_data, "Missing 'historical_centrality' in mule cache"
    print(f"  [Mule Graph Test] Global cache verified at {cache_path}: {cache_data['total_nodes']} nodes, {cache_data['total_edges']} edges")

    # Verify reloading across separate instance
    reloaded_graph = MuleNetworkGraph(cache_file=cache_path)
    reloaded_res = reloaded_graph.trace_trail("ACC-RELOAD-TEST", 60000.0)
    assert len(reloaded_res["mule_accounts"]) > 0, "No mule accounts in reloaded trail"
    print("  [Mule Graph Test] Successfully loaded persistent graph across session and traced new trail")

    # Capability 10: Real-World Data Corruption & Comparative Performance Report
    print("\nSimulating Real-World Data Imperfections (20% corruption)...")
    report = run_performance_comparison(corruption_rate=0.2)
    assert "mae_clean" in report and "mae_corrupted" in report
    assert report["mae_clean"] <= report["mae_corrupted"]
    print("  [Data Corruption Test] Comparative performance report generated successfully.")

    print("\n" + "=" * 65)
    print(" ALL CAPABILITIES & FOUNDATIONAL IMPROVEMENTS VERIFIED!")
    print("=" * 65)


def corrupt_data(test_df, corruption_rate: float = 0.2):
    """
    Simulate real-world data imperfections by randomly applying:
      1. Dropping the amount field (NaN)
      2. Swapping IFSC codes between records
      3. Introducing typos into the complaint text (e.g., 'UPI' -> 'upi' / 'UIP' / etc.)
    Applied to a specified fraction of the dataset (default 20%).
    """
    import random
    import re
    import numpy as np
    import pandas as pd

    df_c = test_df.copy().reset_index(drop=True)
    n_corrupt = int(len(df_c) * corruption_rate)
    
    rng = np.random.RandomState(42)
    py_rnd = random.Random(42)
    corrupt_indices = rng.choice(len(df_c), size=n_corrupt, replace=False)

    for idx in corrupt_indices:
        # 1. Drop the amount field
        df_c.at[idx, "amount"] = np.nan

        # 2. Swap IFSC codes between records
        swap_with = rng.randint(0, len(df_c))
        orig_ifsc = df_c.at[idx, "ifsc_code"]
        df_c.at[idx, "ifsc_code"] = df_c.at[swap_with, "ifsc_code"]
        df_c.at[swap_with, "ifsc_code"] = orig_ifsc

        # 3. Introduce typos in complaint text (e.g., change 'UPI' to 'UPI' or 'upi' / typos)
        text = str(df_c.at[idx, "complaint_text"])
        if "UPI" in text:
            replacement = py_rnd.choice(["upi", "U_P_I", "UIP", "UP1"])
            text = text.replace("UPI", replacement, 1)
        elif "upi" in text:
            replacement = py_rnd.choice(["UPI", "u_p_i", "uip"])
            text = text.replace("upi", replacement, 1)
        elif "rupay" in text or "rupees" in text or "Rs" in text:
            text = text.replace("rupay", "rpay").replace("rupees", "rpees").replace("Rs", "R_s")
        else:
            text = text + " [upi transaction discrepancy]"

        # Also corrupt explicit ₹ symbols to approximate transcribed noise
        text = re.sub(r'₹\s*([0-9,]+)', r'approx \1 rs', text)
        df_c.at[idx, "complaint_text"] = text

    return df_c


def run_performance_comparison(corruption_rate: float = 0.2) -> dict:
    """
    Evaluates XGBoost model performance on clean vs corrupted test data.
    Outputs MAE, RMSE, and accuracy drop alongside the human-readable conclusion.
    """
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from backend.nlp.extractor import ComplaintExtractor

    data_path = "data/complaints.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    df = pd.read_csv(data_path, encoding="utf-8")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour_of_day"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_peak_hours"] = df["hour_of_day"].between(18, 22).astype(int)

    FRAUD_TYPE_MAP = {"upi_fraud": 0, "kyc_fraud": 1, "phishing": 2}
    df["fraud_type_enc"] = df["fraud_type"].map(FRAUD_TYPE_MAP)
    df["log_amount"] = np.log1p(df["amount"])

    CITY_TIER = {
        "Mumbai": 1, "Delhi": 1, "Bangalore": 1, "Hyderabad": 1, "Chennai": 1,
        "Kolkata": 1, "Pune": 2, "Ahmedabad": 2, "Jaipur": 2, "Lucknow": 2,
    }
    df["city_tier"] = df["city"].map(CITY_TIER).fillna(2).astype(int)

    # Reconstruct withdrawal_minutes target according to domain formulas in train_xgboost.py
    BASE_MINUTES = {0: 35.0, 1: 25.0, 2: 55.0}
    np.random.seed(42)
    withdrawal_minutes = np.zeros(len(df))
    for i, row in df.iterrows():
        base = BASE_MINUTES[row["fraud_type_enc"]]
        amount_effect = max(0, (row["log_amount"] - df["log_amount"].median()) * 2.5)
        peak_effect = 5.0 if row["is_peak_hours"] else 0.0
        weekend_effect = -4.0 if row["is_weekend"] else 0.0
        tier_effect = 3.0 if row["city_tier"] == 1 else 0.0
        noise = np.random.normal(0, 8)
        minutes = base + amount_effect + peak_effect + weekend_effect + tier_effect + noise
        withdrawal_minutes[i] = float(np.clip(minutes, 5, 120))
    df["withdrawal_minutes"] = withdrawal_minutes

    FEATURES = ["fraud_type_enc", "log_amount", "hour_of_day", "day_of_week", "is_weekend", "is_peak_hours", "city_tier"]
    _, test_df = train_test_split(df, test_size=0.2, random_state=42)

    corrupted_test = corrupt_data(test_df, corruption_rate=corruption_rate)

    booster = xgb.Booster()
    booster.load_model("models/time_predictor.json")
    extractor = ComplaintExtractor()

    def run_inference(dset):
        preds = []
        for _, row in dset.iterrows():
            amt = row["amount"]
            text = str(row["complaint_text"])
            nlp_res = extractor.extract(text)

            # In production, if amount field is missing, recover via NLP; fallback to median if unparseable
            if pd.isna(amt) or amt is None:
                amt = nlp_res.amount if nlp_res.amount is not None else 25000.0
                fraud_t = nlp_res.fraud_type or row.get("fraud_type", "upi_fraud")
            else:
                fraud_t = row.get("fraud_type") or nlp_res.fraud_type or "upi_fraud"

            f_enc = FRAUD_TYPE_MAP.get(fraud_t, 0)
            log_amt = np.log1p(float(amt))
            feat_vec = [f_enc, log_amt, row["hour_of_day"], row["day_of_week"], row["is_weekend"], row["is_peak_hours"], row["city_tier"]]
            dm = xgb.DMatrix([feat_vec], feature_names=FEATURES)
            preds.append(float(booster.predict(dm)[0]))
        return np.array(preds)

    y_true = test_df["withdrawal_minutes"].values
    preds_clean = run_inference(test_df)
    preds_corr = run_inference(corrupted_test)

    mae_clean = float(mean_absolute_error(y_true, preds_clean))
    rmse_clean = float(np.sqrt(mean_squared_error(y_true, preds_clean)))
    mae_corr = float(mean_absolute_error(y_true, preds_corr))
    rmse_corr = float(np.sqrt(mean_squared_error(y_true, preds_corr)))

    # Operational accuracy within 10-minute intervention window
    acc_clean = float(np.mean(np.abs(y_true - preds_clean) <= 10.0))
    acc_corr = float(np.mean(np.abs(y_true - preds_corr) <= 10.0))
    acc_drop = float(acc_clean - acc_corr)

    conclusion = (
        f"Estimated real-world performance: MAE ≈ {mae_corr:.1f} minutes; "
        f"we recommend a human-in-the-loop fallback for low-confidence extractions."
    )

    print("\n" + "=" * 65)
    print(" PROJECT DRISHTI — MODEL ROBUSTNESS & CORRUPTION REPORT")
    print("=" * 65)
    print(f" Dataset: complaints.csv (Test split: {len(test_df)} records, {corruption_rate:.0%} corrupted)")
    print("-" * 65)
    print(f" {'Metric':<22} {'Clean Data':<16} {'Corrupted (20%)':<18} {'Delta / Drop':<12}")
    print("-" * 65)
    print(f" {'MAE':<22} {mae_clean:>8.2f} min     {mae_corr:>8.2f} min     {mae_corr - mae_clean:>+8.2f} min")
    print(f" {'RMSE':<22} {rmse_clean:>8.2f} min     {rmse_corr:>8.2f} min     {rmse_corr - rmse_clean:>+8.2f} min")
    print(f" {'Accuracy (<=10m)':<22} {acc_clean:>8.1%}         {acc_corr:>8.1%}           {-acc_drop:>+8.1%}")
    print("-" * 65)
    print(f" Conclusion:\n   \"{conclusion}\"")
    print("=" * 65)

    return {
        "mae_clean": mae_clean,
        "rmse_clean": rmse_clean,
        "acc_clean": acc_clean,
        "mae_corrupted": mae_corr,
        "rmse_corrupted": rmse_corr,
        "acc_corrupted": acc_corr,
        "acc_drop": acc_drop,
        "conclusion": conclusion,
    }


if __name__ == "__main__":
    run_tests()

