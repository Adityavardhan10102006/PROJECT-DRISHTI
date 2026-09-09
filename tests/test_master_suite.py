"""
tests/test_master_suite.py — Project DRISHTI
============================================
Comprehensive Automated Pytest Suite covering:
  1. Data layer integrity (ATM dataset, Transactions dataset, Police units)
  2. Multi-hop Money Trail Graph Analysis & NetworkX metrics
  3. ML Models (Risk classifier, Amount regressor, Time window predictor)
  4. SHAP TreeExplainer feature attributions & human badges
  5. Top-K Candidate ATM Ranking (Geospatial candidate filtering, distance, risk score)
  6. Police Response Feasibility & ETA calculations
  7. API validation & error handling (invalid coords, negative amount, missing text)
  8. End-to-end execution of all 5 Demo Cases from data/demo_cases.json
  9. Continuous Retraining with Candidate Model Evaluation Gate
  10. Real-time Transaction Simulator controls
"""

import os
import json
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from main import app
from backend.ml.amount_predictor import get_amount_predictor
from backend.ml.time_predictor import TimeWindowPredictor
from backend.ml.risk_predictor import get_risk_predictor
from backend.ml.mule_graph import get_mule_graph
from backend.clustering.hotspot import evaluate_candidate_atms
from backend.ml.feasibility import get_feasibility_engine
from backend.ml.retrain_feedback import run_continuous_retraining
from backend.services.transaction_simulator import get_transaction_simulator


client = TestClient(app)


# ── 1. Data Layer Tests ──────────────────────────────────────────
def test_atm_dataset_exists_and_valid():
    atm_path = "data/hyderabad_atms.csv"
    assert os.path.exists(atm_path), f"{atm_path} must exist"
    df = pd.read_csv(atm_path)
    assert len(df) >= 150, "Dataset should have sufficient ATM records"
    required_cols = ["atm_id", "bank", "latitude", "longitude", "area", "locality", "city", "pincode", "is_24x7"]
    for col in required_cols:
        assert col in df.columns, f"Missing {col} in hyderabad_atms.csv"
    assert (df["latitude"].between(17.0, 17.8)).all(), "All ATMs should be within Hyderabad latitude"
    assert (df["longitude"].between(78.1, 78.8)).all(), "All ATMs should be within Hyderabad longitude"


def test_transactions_dataset_exists_and_valid():
    tx_path = "data/transactions.csv"
    assert os.path.exists(tx_path), f"{tx_path} must exist"
    df = pd.read_csv(tx_path)
    assert len(df) >= 5000, "Transactions dataset should have sufficient training records"
    required_cols = [
        "transaction_id", "source_account", "destination_account", "amount", "timestamp",
        "transaction_type", "fraud_type", "source_latitude", "source_longitude",
        "destination_latitude", "destination_longitude", "source_bank", "destination_bank",
        "device_id", "ip_risk_score", "is_fraud", "hop_number"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing {col} in transactions.csv"
    assert (df["amount"] > 0).all(), "All transaction amounts must be positive"


def test_police_units_exists_and_valid():
    police_path = "data/police_units.json"
    assert os.path.exists(police_path), f"{police_path} must exist"
    with open(police_path, "r", encoding="utf-8") as f:
        units = json.load(f)
    assert len(units) >= 15, "Should have patrol units across Hyderabad jurisdictions"
    for u in units:
        assert "unit_id" in u and "name" in u and "jurisdiction" in u
        assert ("lat" in u or "latitude" in u) and ("lon" in u or "longitude" in u)


# ── 2. ML Models & Evaluation Metrics Tests ──────────────────────
def test_metrics_json_has_genuine_metrics():
    metrics_path = "models/metrics.json"
    assert os.path.exists(metrics_path), "models/metrics.json must exist"
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    
    assert "risk_model" in metrics
    assert "accuracy" in metrics["risk_model"]
    assert "f1" in metrics["risk_model"]
    assert "roc_auc" in metrics["risk_model"]
    assert 0.60 <= metrics["risk_model"]["accuracy"] <= 1.0

    assert "amount_model" in metrics
    assert "mae" in metrics["amount_model"]
    assert "rmse" in metrics["amount_model"]
    assert "r2" in metrics["amount_model"]
    assert metrics["amount_model"]["r2"] > 0.90

    assert "time_model" in metrics
    assert "mae" in metrics["time_model"]
    assert metrics["time_model"]["mae"] < 15.0


def test_amount_predictor_regression():
    pred = get_amount_predictor()
    res = pred.predict(
        amount=100000.0,
        fraud_type="upi_fraud",
        hop_count=3,
        hour=15,
        day_of_week=2,
    )
    assert "predicted_cashout_amount" in res
    assert "lower_bound" in res and "upper_bound" in res
    assert res["lower_bound"] <= res["predicted_cashout_amount"] <= res["upper_bound"]
    assert 0 < res["predicted_cashout_amount"] <= 100000.0


def test_time_predictor():
    time_model = TimeWindowPredictor()
    res = time_model.predict(
        amount=85000.0,
        fraud_type="upi_fraud",
        city="Hyderabad",
    )
    assert hasattr(res, "peak_minutes")
    assert hasattr(res, "earliest_minutes") and hasattr(res, "latest_minutes")
    assert res.earliest_minutes <= res.peak_minutes <= res.latest_minutes


def test_risk_predictor_and_shap():
    from datetime import datetime, timezone
    rp = get_risk_predictor()
    res = rp.predict(
        fraud_type="upi_fraud",
        amount=95000.0,
        hop_count=3,
        centrality=0.25,
        complaint_dt=datetime(2026, 9, 1, 22, 0, tzinfo=timezone.utc),
        city_tier=1,
        est_withdrawal_mins=35,
    )
    assert 0.0 <= res["risk_score"] <= 100.0
    assert res["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "explanation" in res and len(res["explanation"]) > 0
    # Verify SHAP fields
    first_exp = res["explanation"][0]
    assert "feature" in first_exp
    assert "contribution" in first_exp
    assert "direction" in first_exp
    assert "badge" in first_exp


# ── 3. Candidate ATM Geospatial Ranking ───────────────────────────
def test_candidate_atm_ranking():
    from backend.clustering.hotspot import load_atm_dataset, filter_candidate_atms, score_candidate_atms, rank_candidate_atms

    atms = load_atm_dataset()
    assert len(atms) >= 150, "Should load full ATM dataset"
    filtered = filter_candidate_atms(atms, 17.3850, 78.4867, max_radius_km=30.0)
    assert len(filtered) > 0, "Should filter candidates within radius"
    scored = score_candidate_atms(filtered, 17.3850, 78.4867, amount=85000.0)
    assert len(scored) == len(filtered)
    ranked_top = rank_candidate_atms(scored, k=5, amount=85000.0)
    assert len(ranked_top) == 5

    ranked = evaluate_candidate_atms(
        victim_lat=17.3850,
        victim_lon=78.4867,
        amount=85000.0,
        top_k=5,
    )
    assert len(ranked) == 5
    assert ranked[0]["rank"] == 1
    # Check that it's sorted descending by risk_score
    scores = [r["risk_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
    for r in ranked:
        assert "atm_id" in r and "bank" in r and "distance_km" in r
        assert r["distance_km"] >= 0.0


# ── 4. Money Trail NetworkX Graph ────────────────────────────────
def test_mule_graph_features():
    mg = get_mule_graph()
    trail = mg.trace_trail(initial_amount=75000.0, starting_account="ACC-TEST-1234")
    assert trail["hop_count"] >= 1
    assert "mule_accounts" in trail
    assert "graph_metrics" in trail
    assert "data_source" in trail
    assert trail["data_source"] in ["synthetic_demo_dataset", "transaction_dataset", "synthetic_fallback"]
    metrics = trail["graph_metrics"]
    assert "in_degree" in metrics
    assert "out_degree" in metrics
    assert "data_source" in metrics


# ── 5. Police Feasibility Engine ─────────────────────────────────
def test_police_feasibility():
    fe = get_feasibility_engine()
    res = fe.evaluate_location_feasibility(
        target_lat=17.4123,
        target_lon=78.4489,
        peak_withdrawal_minutes=40,
        case_risk_score=85.0,
    )
    assert "unit_name" in res
    assert "eta_minutes" in res
    assert res["eta_minutes"] > 0
    assert "time_margin_minutes" in res
    assert "feasibility_status" in res


# ── 6. API Validation & Error Handling ───────────────────────────
def test_api_validation_errors():
    # Missing complaint text
    res = client.post("/predict/", json={})
    assert res.status_code == 422

    # Invalid latitude
    res = client.post("/predict/", json={
        "complaint_text": "Fraud complaint",
        "victim_lat": 150.0,
        "victim_lon": 78.4,
    })
    assert res.status_code == 422

    # Invalid longitude
    res = client.post("/predict/", json={
        "complaint_text": "Fraud complaint",
        "victim_lat": 17.4,
        "victim_lon": 250.0,
    })
    assert res.status_code == 422

    # Negative amount
    res = client.post("/predict/", json={
        "complaint_text": "Fraud complaint",
        "amount": -500.0,
    })
    assert res.status_code == 422


# ── 7. End-to-End Test for 5 Demo Cases ───────────────────────────
def test_all_five_demo_cases():
    demo_file = "data/demo_cases.json"
    assert os.path.exists(demo_file)
    with open(demo_file, "r", encoding="utf-8") as f:
        cases = json.load(f)
    assert len(cases) == 5

    for case in cases:
        payload = case["payload"]
        res = client.post("/predict/", json=payload)
        assert res.status_code == 200, f"Failed case {case['case_id']}: {res.text}"
        data = res.json()

        # 5D Assertions
        assert "five_d" in data
        assert "where" in data["five_d"]
        assert "when" in data["five_d"]
        assert "amount" in data["five_d"]
        assert "why" in data["five_d"]
        assert "action" in data["five_d"]

        # Top-K
        assert len(data.get("top_k_locations", [])) > 0
        # Risk score
        assert 0.0 <= data["risk_score"] <= 100.0
        # Feasibility
        assert data.get("feasibility") is not None

        # Data Provenance & Source Labeling Assertions
        assert "data_sources" in data
        assert "transactions" in data["data_sources"]
        assert "atm_locations" in data["data_sources"]
        assert "police_units" in data["data_sources"]
        assert "money_trail" in data and "data_source" in data["money_trail"]
        assert data["money_trail"]["data_source"] in ["synthetic_demo_dataset", "transaction_dataset", "synthetic_fallback"]
        assert "time_window" in data and "model_source" in data["time_window"]
        assert data["time_window"]["model_source"] in ["xgboost", "rule_based_fallback"]


# ── 8. Continuous Retraining Gate Test ────────────────────────────
def test_continuous_retraining_gate():
    res = run_continuous_retraining()
    assert res["status"] == "success"
    assert "promoted" in res
    assert "candidate_metrics" in res
    assert res["candidate_metrics"]["f1_score"] >= 0.60


# ── 9. Transaction Simulator Test ────────────────────────────────
def test_transaction_simulator_lifecycle():
    sim = get_transaction_simulator()
    status = sim.get_status()
    assert status["mode"] == "DEMO / SIMULATION MODE"
    
    start_res = sim.start(interval_seconds=1.0)
    assert start_res["status"] in ["started", "already_running"]

    # Verify API status endpoint
    res = client.get("/api/simulation/status")
    assert res.status_code == 200
    assert res.json()["mode"] == "DEMO / SIMULATION MODE"

    stop_res = sim.stop()
    assert stop_res["status"] in ["stopped", "already_stopped"]
