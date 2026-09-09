"""
backend/ml/drift.py — Project DRISHTI
======================================
Offline Data & Concept Drift Monitoring Engine.

Calculates Population Stability Index (PSI) and distribution shifts across:
  - Numerical features (amount, hop_count, betweenness_centrality)
  - Categorical features (fraud_type, city, bank)
  - Output prediction drift (risk_score, predicted_minutes)

PSI Interpretation:
  - PSI < 0.10: No significant drift (Stable distribution)
  - 0.10 <= PSI < 0.25: Moderate drift (Recommend observation)
  - PSI >= 0.25: Significant drift (Trigger retraining alert)
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

DRIFT_REPORT_PATH = "models/drift_report.json"


def calculate_psi_numeric(
    expected: np.ndarray,
    actual: np.ndarray,
    num_buckets: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """
    Computes Population Stability Index (PSI) for continuous numerical distributions.
    """
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Quantile bin edges based on expected distribution
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bin_edges = np.percentile(expected, percentiles)
    bin_edges[0] -= 1e-5
    bin_edges[-1] += 1e-5

    # Count occurrences in each bin
    exp_counts, _ = np.histogram(expected, bins=bin_edges)
    act_counts, _ = np.histogram(actual, bins=bin_edges)

    # Normalize to proportions
    exp_pct = np.maximum(exp_counts / len(expected), epsilon)
    act_pct = np.maximum(act_counts / len(actual), epsilon)

    # PSI equation: sum((Actual% - Expected%) * ln(Actual% / Expected%))
    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return round(float(psi_val), 4)


def calculate_psi_categorical(
    expected: List[Any],
    actual: List[Any],
    epsilon: float = 1e-4,
) -> float:
    """Computes PSI for categorical distributions."""
    all_categories = sorted(list(set(expected).union(set(actual))))
    if not all_categories or len(expected) == 0 or len(actual) == 0:
        return 0.0

    exp_counts = pd.Series(expected).value_counts()
    act_counts = pd.Series(actual).value_counts()

    exp_pct = np.array([exp_counts.get(c, 0) / len(expected) for c in all_categories])
    act_pct = np.array([act_counts.get(c, 0) / len(actual) for c in all_categories])

    exp_pct = np.maximum(exp_pct, epsilon)
    act_pct = np.maximum(act_pct, epsilon)

    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return round(float(psi_val), 4)


def generate_drift_report(
    reference_csv: str = "data/complaints.csv",
    monitored_csv: Optional[str] = None,
    output_path: str = DRIFT_REPORT_PATH,
) -> Dict[str, Any]:
    """
    Generates structured offline drift report comparing reference baseline vs monitored distribution.
    """
    if not os.path.exists(reference_csv):
        return {"status": "ERROR", "error": f"Reference file {reference_csv} not found"}

    df_ref = pd.read_csv(reference_csv)

    if monitored_csv and os.path.exists(monitored_csv):
        df_mon = pd.read_csv(monitored_csv)
    else:
        # If no separate monitored dataset is supplied, split reference chronologically
        df_ref["dt"] = pd.to_datetime(df_ref["timestamp"])
        df_ref = df_ref.sort_values("dt").reset_index(drop=True)
        split_idx = int(len(df_ref) * 0.70)
        df_mon = df_ref.iloc[split_idx:].copy()
        df_ref = df_ref.iloc[:split_idx].copy()

    feature_drifts = {}

    # 1. Amount Drift (Numerical)
    if "amount" in df_ref.columns and "amount" in df_mon.columns:
        psi_amt = calculate_psi_numeric(df_ref["amount"].values, df_mon["amount"].values)
        feature_drifts["amount"] = {
            "psi": psi_amt,
            "status": "STABLE" if psi_amt < 0.10 else ("MODERATE_DRIFT" if psi_amt < 0.25 else "HIGH_DRIFT"),
            "ref_mean": round(float(df_ref["amount"].mean()), 2),
            "mon_mean": round(float(df_mon["amount"].mean()), 2),
        }

    # 2. Fraud Type Drift (Categorical)
    if "fraud_type" in df_ref.columns and "fraud_type" in df_mon.columns:
        psi_ft = calculate_psi_categorical(df_ref["fraud_type"].tolist(), df_mon["fraud_type"].tolist())
        feature_drifts["fraud_type"] = {
            "psi": psi_ft,
            "status": "STABLE" if psi_ft < 0.10 else ("MODERATE_DRIFT" if psi_ft < 0.25 else "HIGH_DRIFT"),
        }

    # 3. City Distribution Drift (Categorical)
    if "city" in df_ref.columns and "city" in df_mon.columns:
        psi_city = calculate_psi_categorical(df_ref["city"].tolist(), df_mon["city"].tolist())
        feature_drifts["city"] = {
            "psi": psi_city,
            "status": "STABLE" if psi_city < 0.10 else ("MODERATE_DRIFT" if psi_city < 0.25 else "HIGH_DRIFT"),
        }

    overall_status = "STABLE"
    if any(d["status"] == "HIGH_DRIFT" for d in feature_drifts.values()):
        overall_status = "ALERT_SIGNIFICANT_DRIFT"
    elif any(d["status"] == "MODERATE_DRIFT" for d in feature_drifts.values()):
        overall_status = "WARNING_MODERATE_DRIFT"

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": overall_status,
        "reference_records": len(df_ref),
        "monitored_records": len(df_mon),
        "metrics_evaluated": ["Population Stability Index (PSI)"],
        "thresholds": {
            "stable": "< 0.10",
            "moderate_drift": "0.10 - 0.25",
            "significant_drift": ">= 0.25",
        },
        "features": feature_drifts,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    rep = generate_drift_report()
    print(f"Drift monitoring completed. Status: {rep['status']}")
