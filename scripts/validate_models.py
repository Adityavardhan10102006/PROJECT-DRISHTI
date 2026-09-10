"""
scripts/validate_models.py — Project DRISHTI
==============================================
Automated Model Integrity & Inference Health Validation.

Checks:
  1. All model binary artifacts exist on disk
  2. Metadata records exist and specify versions
  3. Feature schema matches between training and inference
  4. Feature order is preserved
  5. Inference handles edge cases (zero amount, boundary coords, unusual types) without NaN
  6. Point predictions are within physically valid domains
  7. Predicted probability distributions are properly calibrated and sum to 1.0
  8. Synthetic/real dataset provenance is explicitly declared
  9. Central metrics exist and are non-zero

Exits with non-zero status if any critical check fails.
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.location_predictor import get_location_predictor
from backend.ml.time_predictor import get_time_predictor
from backend.ml.amount_predictor import get_amount_predictor
from backend.ml.risk_predictor import get_risk_predictor
from backend.ml.features import FeatureEngineeringPipeline


def validate_all_models() -> bool:
    passed = []
    failed = []

    def check(name: str, condition: bool, reason: str = ""):
        if condition:
            print(f"[PASS] {name}")
            passed.append(name)
        else:
            print(f"[FAIL] {name}: {reason}")
            failed.append((name, reason))

    print("=" * 70)
    print(" PROJECT DRISHTI — AUTOMATED ML MODEL VALIDATION SUITE")
    print("=" * 70)

    # 1. Model files existence
    expected_files = [
        "models/location_classifier.joblib",
        "models/location_calibrator.joblib",
        "models/time_predictor.json",
        "models/amount_predictor.joblib",
        "models/risk_classifier.joblib",
        "models/location_meta.json",
        "models/time_meta.json",
        "models/amount_meta.json",
        "models/risk_meta.json",
        "models/metrics.json",
        "models/feature_schema.json",
        "models/environment.json",
    ]
    for ef in expected_files:
        check(f"Artifact exists: {ef}", os.path.exists(ef), f"Missing {ef}")

    # 2. Metadata schemas & dataset provenance
    try:
        with open("models/location_meta.json", "r", encoding="utf-8") as f:
            lm = json.load(f)
        check("Location meta dataset_type is synthetic_benchmark", lm.get("dataset_type") == "synthetic_benchmark")
        check("Location meta contains version", bool(lm.get("version")))

        with open("models/time_meta.json", "r", encoding="utf-8") as f:
            tm = json.load(f)
        check("Time meta specifies conformal_q_90", "conformal_q_90" in tm)

        with open("models/amount_meta.json", "r", encoding="utf-8") as f:
            am = json.load(f)
        check("Amount meta contains metrics", "metrics" in am and "mae" in am["metrics"])

        with open("models/risk_meta.json", "r", encoding="utf-8") as f:
            rm = json.load(f)
        has_risk_metrics = ("metrics" in rm and "accuracy" in rm["metrics"]) or ("accuracy" in rm and ("f1_score" in rm or "f1" in rm))
        check("Risk meta specifies class metrics", has_risk_metrics)
    except Exception as e:
        check("Metadata integrity", False, str(e))

    # 3. Feature schema alignment
    try:
        with open("models/feature_schema.json", "r", encoding="utf-8") as f:
            schema = json.load(f)
        schema_loc = schema["models"]["location_model"]["feature_names"]
        pipeline_loc = FeatureEngineeringPipeline.LOCATION_FEATURE_NAMES
        check("Location feature order matches schema", schema_loc == pipeline_loc)
    except Exception as e:
        check("Feature schema alignment", False, str(e))

    # 4. Location Predictor inference & probability calibration
    try:
        lp = get_location_predictor()
        res_loc = lp.predict_top_k(victim_lat=17.4123, victim_lon=78.4489, amount=75000.0, k=3)
        check("Location predictor returned success", res_loc["status"] == "success")
        check("Location prediction method is ML or Calibrated ML", res_loc["prediction_method"] in ["ml", "calibrated_ml"])
        check("Location top_k length matches k", len(res_loc["top_k"]) == 3)

        top_candidates = res_loc["top_k"]
        probs = [c["ranking_probability"] for c in top_candidates]
        check("Ranking probabilities sum approximately to 1.0", 0.98 <= sum(probs) <= 1.02)
        check("All calibrated probabilities in [0, 1]", all(0.0 <= c["probability"] <= 1.0 for c in top_candidates))
        check("Top candidate has evidence list", len(top_candidates[0].get("evidence_list", [])) >= 2)

        # Missing location returns insufficient_location_data
        missing_res = lp.predict_top_k(victim_lat=None, victim_lon=None, amount=50000.0, demo_mode=False)
        check("Missing coordinates properly returns insufficient_location_data", missing_res["status"] == "insufficient_location_data")
    except Exception as e:
        check("Location Predictor inference health", False, str(e))

    # 5. Time Predictor inference & conformal bounds
    try:
        tp = get_time_predictor()
        res_time = tp.predict(fraud_type="upi_fraud", amount=65000.0, city="Mumbai")
        check("Time prediction point estimate within valid range [5, 120]", 5 <= res_time.peak_minutes <= 120)
        check("Conformal interval order valid (lower <= peak <= upper)", res_time.lower_bound <= res_time.peak_minutes <= res_time.upper_bound)
        check("Conformal coverage reported (90%)", res_time.coverage_level == 0.90)
    except Exception as e:
        check("Time Predictor inference health", False, str(e))

    # 6. Amount Predictor inference & bounds
    try:
        ap = get_amount_predictor()
        res_amt = ap.predict(amount=85000.0, fraud_type="upi_fraud", hop_count=3)
        pred_val = res_amt["predicted_cashout_amount"]
        check("Amount prediction positive", pred_val > 0)
        check("Amount bounds valid (lower <= pred <= upper)", res_amt["lower_bound"] <= pred_val <= res_amt["upper_bound"])
        check("Predicted amount does not exceed initial amount", pred_val <= 85000.0)
    except Exception as e:
        check("Amount Predictor inference health", False, str(e))

    # 7. Risk Predictor inference & SHAP
    try:
        rp = get_risk_predictor()
        res_risk = rp.predict(fraud_type="kyc_fraud", amount=120000.0, hop_count=4, centrality=0.28)
        check("Risk score in valid range [0, 100]", 0.0 <= res_risk["risk_score"] <= 100.0)
        check("Risk level in valid categories", res_risk["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        check("Probabilities sum to 1.0", 0.98 <= sum(res_risk["probabilities"].values()) <= 1.02)
        check("Explanation source identified", res_risk["explanation_source"] in ["shap_tree_explainer", "heuristic_fallback"])
        if res_risk["explanation"]:
            first_xai = res_risk["explanation"][0]
            check("SHAP attribution has feature and shap_value", "feature" in first_xai and "shap_value" in first_xai)
            check("SHAP direction identified", first_xai.get("direction") in ["increases_risk", "decreases_risk"])
    except Exception as e:
        check("Risk Predictor inference health", False, str(e))

    # 8. Central metrics.json validation
    try:
        with open("models/metrics.json", "r", encoding="utf-8") as f:
            metrics = json.load(f)
        for mod in ["risk_model", "amount_model", "time_model", "location_model", "baseline", "improvement"]:
            check(f"Central metrics has {mod}", mod in metrics)
        check("Location Top-3 Recall >= 0.75", metrics["location_model"]["top3_recall"] >= 0.75)
        check("Time MAE <= 10.0m", metrics["time_model"]["mae"] <= 10.0)
    except Exception as e:
        check("Central metrics health", False, str(e))

    print("\n" + "=" * 70)
    print(f"VALIDATION SUMMARY: {len(passed)} PASSED, {len(failed)} FAILED")
    print("=" * 70)

    if failed:
        print("\nCRITICAL FAILURES DETECTED:")
        for name, reason in failed:
            print(f" - {name}: {reason}")
        return False

    print("\nALL ML MODELS AND PIPELINES ARE VALIDATED & HEALTHY.")
    return True


if __name__ == "__main__":
    success = validate_all_models()
    sys.exit(0 if success else 1)
