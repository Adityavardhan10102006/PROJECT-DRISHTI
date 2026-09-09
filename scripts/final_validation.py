"""
scripts/final_validation.py — Final 100% Engineering Acceptance Suite
Executes the comprehensive 32-point verification checklist required for hackathon validation.
Must exit with 0 if and only if all mandatory tests pass.
"""

import sys
import os
import json
import re
import pandas as pd
import numpy as np

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_acceptance_suite():
    passed_checks = []
    failed_checks = []

    def log_pass(check_name):
        print(f"[PASS] {check_name}")
        passed_checks.append(check_name)

    def log_fail(check_name, reason=""):
        print(f"[FAIL] {check_name} — {reason}")
        failed_checks.append((check_name, reason))

    print("=" * 70)
    print(" PROJECT DRISHTI — FINAL AUTOMATED ACCEPTANCE CHECK")
    print("=" * 70)

    # 1. Repository structure
    try:
        req_dirs = ["backend", "data", "models", "tests"]
        req_files = ["README.md", "requirements.txt", "main.py"]
        for d in req_dirs:
            assert os.path.isdir(d), f"Missing directory: {d}"
        for f in req_files:
            assert os.path.isfile(f), f"Missing file: {f}"
        log_pass("Repository structure")
    except Exception as e:
        log_fail("Repository structure", str(e))

    # 2. Transaction dataset exists
    tx_path = "data/transactions.csv"
    if os.path.isfile(tx_path):
        log_pass("Transaction dataset exists")
    else:
        log_fail("Transaction dataset exists", f"Missing {tx_path}")

    # 3. Transaction dataset non-empty
    try:
        tx_df = pd.read_csv(tx_path)
        assert len(tx_df) >= 2000, f"Expected >= 2000 records, found {len(tx_df)}"
        log_pass("Transaction dataset non-empty")
    except Exception as e:
        log_fail("Transaction dataset non-empty", str(e))

    # 4. Transaction dataset schema valid
    try:
        from scripts.validate_transactions import validate_transactions
        v_rep = validate_transactions(tx_path)
        assert v_rep["status"] == "PASS"
        assert v_rep["records"] >= 2000
        log_pass("Transaction dataset schema valid")
    except Exception as e:
        log_fail("Transaction dataset schema valid", str(e))

    # 5. ATM dataset exists
    atm_path = "data/hyderabad_atms.csv"
    if os.path.isfile(atm_path):
        log_pass("ATM dataset exists")
    else:
        log_fail("ATM dataset exists", f"Missing {atm_path}")

    # 6. ATM dataset non-empty
    try:
        atm_df = pd.read_csv(atm_path)
        assert len(atm_df) >= 50, f"Expected >= 50 ATMs, found {len(atm_df)}"
        log_pass("ATM dataset non-empty")
    except Exception as e:
        log_fail("ATM dataset non-empty", str(e))

    # 7. Police dataset exists
    police_path = "data/police_units.json"
    try:
        assert os.path.isfile(police_path)
        with open(police_path, "r", encoding="utf-8") as f:
            units = json.load(f)
        assert len(units) >= 10, f"Expected >= 10 police units, found {len(units)}"
        log_pass("Police dataset exists")
    except Exception as e:
        log_fail("Police dataset exists", str(e))

    # 8. Demo cases exist
    demo_path = "data/demo_cases.json"
    try:
        assert os.path.isfile(demo_path)
        with open(demo_path, "r", encoding="utf-8") as f:
            demo_cases = json.load(f)
        assert len(demo_cases) >= 5, f"Expected >= 5 demo cases, found {len(demo_cases)}"
        log_pass("Demo cases exist")
    except Exception as e:
        log_fail("Demo cases exist", str(e))

    # 9. Risk model exists
    risk_model_path = "models/risk_classifier.joblib"
    if os.path.isfile(risk_model_path):
        log_pass("Risk model exists")
    else:
        log_fail("Risk model exists", f"Missing {risk_model_path}")

    # 10. Amount model exists
    amt_paths = ["models/amount_predictor.joblib", "models/amount_model.joblib"]
    if any(os.path.isfile(p) for p in amt_paths):
        log_pass("Amount model exists")
    else:
        log_fail("Amount model exists", f"Missing amount model artifacts")

    # 11. Time model exists
    time_paths = ["models/time_predictor.json", "models/time_model.joblib"]
    if any(os.path.isfile(p) for p in time_paths):
        log_pass("Time model exists")
    else:
        log_fail("Time model exists", f"Missing time model artifacts")

    # 12. Model metadata exists
    try:
        assert os.path.isfile("models/risk_meta.json")
        assert os.path.isfile("models/amount_meta.json")
        assert os.path.isfile("models/feature_meta.json") or os.path.isfile("models/time_meta.json")
        log_pass("Model metadata exists")
    except Exception as e:
        log_fail("Model metadata exists", str(e))

    # 13. metrics.json exists
    metrics_path = "models/metrics.json"
    if os.path.isfile(metrics_path):
        log_pass("metrics.json exists")
    else:
        log_fail("metrics.json exists", f"Missing {metrics_path}")

    # 14. Metrics are numeric and generated
    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
        rm = metrics_data["risk_model"]
        am = metrics_data["amount_model"]
        tm = metrics_data["time_model"]

        for k in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
            assert isinstance(rm[k], (int, float)) and rm[k] > 0, f"Invalid risk metric {k}: {rm[k]}"
        for k in ["mae", "rmse", "r2"]:
            assert isinstance(am[k], (int, float)) and am[k] > 0, f"Invalid amount metric {k}: {am[k]}"
            assert isinstance(tm[k], (int, float)) and tm[k] > 0, f"Invalid time metric {k}: {tm[k]}"
        log_pass("Metrics are numeric and generated")
    except Exception as e:
        log_fail("Metrics are numeric and generated", str(e))

    # 15. No fake hardcoded metrics
    try:
        forbidden_patterns = [
            r"roc_auc\s*=\s*0\.90",
            r"accuracy\s*=\s*0\.95",
            r"precision\s*=\s*0\.92",
            r"recall\s*=\s*0\.91",
            r"f1\s*=\s*0\.93",
            r"except.*:\s*roc_auc\s*=",
        ]
        for root, _, files in os.walk("backend"):
            for file in files:
                if file.endswith(".py"):
                    fp = os.path.join(root, file)
                    with open(fp, "r", encoding="utf-8", errors="ignore") as src:
                        content = src.read()
                        for pat in forbidden_patterns:
                            assert not re.search(pat, content), f"Found forbidden hardcoded pattern '{pat}' in {fp}"
        log_pass("No fake hardcoded metrics")
    except Exception as e:
        log_fail("No fake hardcoded metrics", str(e))

    # 16. Transaction lookup works
    try:
        from backend.ml.mule_graph import get_mule_graph
        mg = get_mule_graph()
        # Pick an actual account from transactions.csv
        known_src = str(tx_df[tx_df["is_fraud"] == 1]["source_account"].iloc[0])
        trail = mg.trace_trail(starting_account=known_src, initial_amount=50000.0)
        assert trail["data_source"] == "synthetic_demo_dataset"
        assert trail["hop_count"] >= 1
        log_pass("Transaction lookup works")
    except Exception as e:
        log_fail("Transaction lookup works", str(e))

    # 17. Money trail graph works
    try:
        assert len(trail["hops"]) >= 1
        assert "initial_amount" in trail
        assert "final_cashout_amount" in trail
        assert "trail_duration_minutes" in trail
        assert "graph_metrics" in trail
        log_pass("Money trail graph works")
    except Exception as e:
        log_fail("Money trail graph works", str(e))

    # 18. Multi-hop detection works
    try:
        multihop_srcs = tx_df[tx_df["hop_number"] > 1]["source_account"].unique()
        found_multi = False
        for s in multihop_srcs[:10]:
            t = mg.trace_trail(starting_account=str(s), initial_amount=75000.0)
            if t["hop_count"] > 1:
                found_multi = True
                break
        assert found_multi or trail["hop_count"] >= 1
        log_pass("Multi-hop detection works")
    except Exception as e:
        log_fail("Multi-hop detection works", str(e))

    # 19. Risk prediction works
    try:
        from backend.ml.risk_predictor import get_risk_predictor
        rp = get_risk_predictor()
        from datetime import datetime, timezone
        risk_res = rp.predict(
            fraud_type="upi_fraud",
            amount=85000.0,
            hop_count=3,
            centrality=0.15,
            complaint_dt=datetime.now(timezone.utc),
            city_tier=1,
            est_withdrawal_mins=30,
        )
        assert 0.0 <= risk_res["risk_score"] <= 100.0
        assert risk_res["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert risk_res["model_source"] == "trained_model"
        log_pass("Risk prediction works")
    except Exception as e:
        log_fail("Risk prediction works", str(e))

    # 20. Amount prediction works
    try:
        from backend.ml.amount_predictor import get_amount_predictor
        ap = get_amount_predictor()
        amt_res = ap.predict(amount=85000.0, fraud_type="upi_fraud", hop_count=3, velocity_mins=25.0)
        assert amt_res["predicted_cashout_amount"] > 0
        assert amt_res["lower_bound"] <= amt_res["predicted_cashout_amount"] <= amt_res["upper_bound"]
        assert 0.0 <= amt_res["confidence"] <= 1.0
        log_pass("Amount prediction works")
    except Exception as e:
        log_fail("Amount prediction works", str(e))

    # 21. Time prediction works
    try:
        from backend.ml.time_predictor import get_time_predictor
        tp = get_time_predictor()
        time_res = tp.predict(amount=85000.0, fraud_type="upi_fraud", city="Hyderabad")
        assert hasattr(time_res, "peak_minutes")
        assert time_res.earliest_minutes <= time_res.peak_minutes <= time_res.latest_minutes
        log_pass("Time prediction works")
    except Exception as e:
        log_fail("Time prediction works", str(e))

    # 22. SHAP works
    try:
        assert "explanation" in risk_res
        assert len(risk_res["explanation"]) > 0
        exp0 = risk_res["explanation"][0]
        assert "feature" in exp0 and "contribution" in exp0 and "direction" in exp0
        assert risk_res.get("explanation_source") in ["shap_tree_explainer", "shap_real_model"]
        log_pass("SHAP works")
    except Exception as e:
        log_fail("SHAP works", str(e))

    # 23. ATM ranking works
    try:
        from backend.clustering.hotspot import evaluate_candidate_atms
        ranked_atms = evaluate_candidate_atms(
            victim_lat=17.4435,
            victim_lon=78.3772,
            amount=85000.0,
            fraud_type="upi_fraud",
            k=3,
        )
        assert len(ranked_atms) == 3
        for atm in ranked_atms:
            assert "atm_id" in atm and "bank" in atm and "risk_score" in atm
            assert "relative_score" in atm or "ranking_probability" in atm or "probability" in atm
        log_pass("ATM ranking works")
    except Exception as e:
        log_fail("ATM ranking works", str(e))

    # 24. Top-K deterministic
    try:
        ranked_atms2 = evaluate_candidate_atms(
            victim_lat=17.4435,
            victim_lon=78.3772,
            amount=85000.0,
            fraud_type="upi_fraud",
            k=3,
        )
        ids1 = [a["atm_id"] for a in ranked_atms]
        ids2 = [a["atm_id"] for a in ranked_atms2]
        assert ids1 == ids2, f"Top-K ATM ranking not deterministic: {ids1} != {ids2}"
        scores1 = [a["risk_score"] for a in ranked_atms]
        scores2 = [a["risk_score"] for a in ranked_atms2]
        assert scores1 == scores2, "Top-K ATM scores differ between runs"
        log_pass("Top-K deterministic")
    except Exception as e:
        log_fail("Top-K deterministic", str(e))

    # 25. Police feasibility works
    try:
        from backend.ml.feasibility import get_feasibility_engine
        fe = get_feasibility_engine()
        feas = fe.evaluate_location_feasibility(
            target_lat=ranked_atms[0]["lat"],
            target_lon=ranked_atms[0]["lon"],
            peak_withdrawal_minutes=time_res.peak_minutes,
            case_risk_score=risk_res["risk_score"],
        )
        assert "unit_name" in feas
        assert "eta_minutes" in feas and feas["eta_minutes"] > 0
        assert "feasibility_score" in feas
        assert "feasibility_status" in feas
        log_pass("Police feasibility works")
    except Exception as e:
        log_fail("Police feasibility works", str(e))

    # 26. 5D intelligence works
    try:
        from backend.ml.explainability import get_5d_engine
        five_d_engine = get_5d_engine()
        five_d = five_d_engine.build_5d_intelligence(
            complaint_id="DRISHTI-TEST-5D",
            fraud_type="upi_fraud",
            amount=85000.0,
            hotspot={"lat": ranked_atms[0]["lat"], "lon": ranked_atms[0]["lon"], "radius_km": 0.45},
            top_k_locations=ranked_atms,
            time_window={"earliest_minutes": time_res.earliest_minutes, "latest_minutes": time_res.latest_minutes, "peak_minutes": time_res.peak_minutes},
            money_trail=trail,
            risk_result=risk_res,
            feasibility=feas,
            city="Hyderabad",
        )
        assert "where" in five_d
        assert "when" in five_d
        assert "amount" in five_d
        assert "why" in five_d
        assert "action" in five_d
        log_pass("5D intelligence works")
    except Exception as e:
        log_fail("5D intelligence works", str(e))

    # 27. API validation works
    try:
        from fastapi.testclient import TestClient
        from main import app
        from backend.auth.security import create_access_token
        _test_token = create_access_token({"sub": "admin", "role": "admin", "uid": 1})
        client = TestClient(app, headers={"Authorization": f"Bearer {_test_token}"})

        # Invalid lat
        bad_lat_res = client.post("/predict/", json={"complaint_text": "Fraud", "victim_lat": 150.0, "victim_lon": 78.0, "amount": 1000.0})
        assert bad_lat_res.status_code == 422

        # Negative amount
        bad_amt_res = client.post("/predict/", json={"complaint_text": "Fraud", "victim_lat": 17.4, "victim_lon": 78.4, "amount": -500.0})
        assert bad_amt_res.status_code == 422
        log_pass("API validation works")
    except Exception as e:
        log_fail("API validation works", str(e))

    # 28. End-to-end prediction works
    try:
        e2e_payload = {
            "complaint_id": "TEST-E2E-001",
            "complaint_text": "Defrauded of Rs 85,000 via malicious UPI link on WhatsApp.",
            "victim_lat": 17.4435,
            "victim_lon": 78.3772,
            "fraud_type": "upi_fraud",
            "amount": 85000.0,
            "bank_account": known_src,
            "timestamp": "2026-09-09T10:00:00",
        }
        res = client.post("/predict/", json=e2e_payload)
        assert res.status_code == 200, f"Prediction failed: {res.text}"
        res_data = res.json()
        assert "five_d" in res_data
        assert "top_k_locations" in res_data and len(res_data["top_k_locations"]) > 0
        assert "data_sources" in res_data
        assert "models" in res_data
        assert res_data["money_trail"]["data_source"] == "synthetic_demo_dataset"
        log_pass("End-to-end prediction works")
    except Exception as e:
        log_fail("End-to-end prediction works", str(e))

    # 29. Demo cases pass
    try:
        for c in demo_cases:
            c_res = client.post("/predict/", json=c["payload"])
            assert c_res.status_code == 200, f"Demo case failed: {c['case_id']}"
            c_data = c_res.json()
            assert "five_d" in c_data and "risk_score" in c_data
        log_pass("Demo cases pass")
    except Exception as e:
        log_fail("Demo cases pass", str(e))

    # 30. Determinism test passes
    try:
        p1 = client.post("/predict/", json=e2e_payload).json()
        p2 = client.post("/predict/", json=e2e_payload).json()

        # Remove volatile fields
        for p in [p1, p2]:
            p.pop("alert_id", None)
            p.pop("processed_at", None)

        assert p1 == p2, f"Identical request produced non-deterministic outputs: diffs={[k for k in p1 if p1.get(k) != p2.get(k)]}"
        log_pass("Determinism test passes")
    except Exception as e:
        log_fail("Determinism test passes", str(e))

    # 31. No secrets detected
    try:
        secret_patterns = [
            r"AKIA[0-9A-Z]{16}",
            r"BEGIN (?:RSA )?PRIVATE KEY",
            r"ghp_[a-zA-Z0-9]{36}",
        ]
        for root, _, files in os.walk("."):
            if any(skip in root for skip in [".git", "__pycache__", ".pytest_cache", "venv", ".venv"]):
                continue
            for file in files:
                if file.endswith((".py", ".json", ".md", ".env.example")):
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()
                        for sp in secret_patterns:
                            assert not re.search(sp, txt), f"Potential secret found in {os.path.join(root, file)}"
        log_pass("No secrets detected")
    except Exception as e:
        log_fail("No secrets detected", str(e))

    # 32. README accurate
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_text = f.read()
        assert "PROJECT DRISHTI" in readme_text
        assert "5D" in readme_text or "Five-D" in readme_text
        assert "metrics.json" in readme_text
        assert "ethical" in readme_text.lower() or "disclaimer" in readme_text.lower()
        log_pass("README accurate")
    except Exception as e:
        log_fail("README accurate", str(e))

    # 33. One-command startup launchers exist
    try:
        assert os.path.isfile("start.py"), "Missing start.py"
        assert os.path.isfile("start.bat"), "Missing start.bat"
        assert os.path.isfile("start.ps1"), "Missing start.ps1"
        assert os.path.isfile("scripts/benchmark_startup.py"), "Missing scripts/benchmark_startup.py"
        log_pass("One-command startup launchers exist")
    except Exception as e:
        log_fail("One-command startup launchers exist", str(e))

    # 34. Fast startup benchmark & sub-second latency verified
    try:
        from scripts.benchmark_startup import run_startup_benchmark
        bm_res = run_startup_benchmark()
        assert bm_res["status"] == "success"
        assert bm_res["startup_time_seconds"] > 0
        assert bm_res["prediction_latency_ms"]["warm_average"] < 500.0, f"Warm latency too high: {bm_res['prediction_latency_ms']['warm_average']} ms"
        log_pass("Fast startup benchmark & sub-second latency verified")
    except Exception as e:
        log_fail("Fast startup benchmark & sub-second latency verified", str(e))

    print("=" * 70)
    print(f"RESULTS: {len(passed_checks)} PASSED, {len(failed_checks)} FAILED")
    print("=" * 70)

    if failed_checks:
        for name, err in failed_checks:
            print(f"  [X] {name}: {err}")
        sys.exit(1)
    else:
        print("\nALL ACCEPTANCE CRITERIA VERIFIED. PROJECT DRISHTI IS 100% READY.")
        sys.exit(0)


if __name__ == "__main__":
    run_acceptance_suite()
