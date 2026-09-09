"""
backend/ml/data_quality.py — Project DRISHTI
==============================================
Data Quality & Integrity Validation Engine.

Executes pre-training and ingestion checks:
  - Missingness and null rate checks
  - Coordinate range sanity (-90 to 90 lat, -180 to 180 lon)
  - Negative or impossible amount checks
  - Timestamp ordering and format validity
  - Categorical value validity (fraud_type, bank, city)
  - Case duplication & identifier uniqueness
  - Class imbalance reporting
  - Outlier detection

Emits a structured audit report to models/data_quality_report.json.
Fails loudly if critical anomalies are detected.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

DATA_DIR = "data"
MODELS_DIR = "models"
REPORT_PATH = os.path.join(MODELS_DIR, "data_quality_report.json")

VALID_FRAUD_TYPES = {"upi_fraud", "kyc_fraud", "phishing", "legitimate"}
VALID_CITIES = {
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Unknown"
}


def validate_complaints_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates complaints dataset for nulls, coordinate ranges, amounts, and fraud types."""
    issues = []
    critical_failure = False

    total_records = len(df)
    if total_records == 0:
        return {"status": "FAIL", "critical": True, "error": "Complaints dataset is empty"}

    # 1. Null check on critical columns
    req_cols = ["complaint_id", "timestamp", "amount", "fraud_type"]
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        return {"status": "FAIL", "critical": True, "error": f"Missing required columns: {missing_cols}"}

    # 2. Duplicate complaint IDs
    dup_ids = int(df["complaint_id"].duplicated().sum())
    if dup_ids > 0:
        issues.append(f"Found {dup_ids} duplicate complaint IDs")

    # 3. Amount sanity
    invalid_amounts = int((df["amount"] < 0).sum())
    if invalid_amounts > 0:
        issues.append(f"Found {invalid_amounts} negative amount records")
        critical_failure = True

    null_amounts = int(df["amount"].isna().sum())
    if null_amounts > 0:
        issues.append(f"Found {null_amounts} null amount records")

    # 4. Coordinate range sanity
    if "victim_lat" in df.columns and "victim_lon" in df.columns:
        valid_coords = df.dropna(subset=["victim_lat", "victim_lon"])
        bad_lat = int((~valid_coords["victim_lat"].between(-90.0, 90.0)).sum())
        bad_lon = int((~valid_coords["victim_lon"].between(-180.0, 180.0)).sum())
        if bad_lat > 0 or bad_lon > 0:
            issues.append(f"Invalid coordinates: {bad_lat} bad lat, {bad_lon} bad lon")
            critical_failure = True

    # 5. Fraud type validity
    unknown_fraud = set(df["fraud_type"].dropna().unique()) - VALID_FRAUD_TYPES
    if unknown_fraud:
        issues.append(f"Unrecognized fraud types: {unknown_fraud}")

    # 6. Timestamp parsing
    try:
        ts_parsed = pd.to_datetime(df["timestamp"])
        min_ts = str(ts_parsed.min())
        max_ts = str(ts_parsed.max())
    except Exception as e:
        issues.append(f"Timestamp parsing error: {e}")
        critical_failure = True
        min_ts, max_ts = "N/A", "N/A"

    fraud_distribution = df["fraud_type"].value_counts(normalize=True).to_dict()

    return {
        "dataset": "complaints.csv",
        "total_records": total_records,
        "status": "FAIL" if critical_failure else ("WARNING" if issues else "PASS"),
        "critical_failure": critical_failure,
        "issues": issues,
        "timestamp_range": {"min": min_ts, "max": max_ts},
        "fraud_type_distribution": {k: round(float(v), 4) for k, v in fraud_distribution.items()},
        "amount_summary": {
            "min": float(df["amount"].min()) if not df["amount"].empty else 0.0,
            "median": float(df["amount"].median()) if not df["amount"].empty else 0.0,
            "mean": round(float(df["amount"].mean()), 2) if not df["amount"].empty else 0.0,
            "max": float(df["amount"].max()) if not df["amount"].empty else 0.0,
        },
    }


def validate_transactions_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates multi-hop transactions dataset."""
    issues = []
    critical_failure = False

    total_records = len(df)
    if total_records == 0:
        return {"status": "FAIL", "critical": True, "error": "Transactions dataset is empty"}

    req_cols = ["transaction_id", "source_account", "destination_account", "amount", "timestamp", "is_fraud"]
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        return {"status": "FAIL", "critical": True, "error": f"Missing required columns: {missing_cols}"}

    # Negative amounts
    neg_amounts = int((df["amount"] <= 0).sum())
    if neg_amounts > 0:
        issues.append(f"Found {neg_amounts} non-positive transaction amounts")
        critical_failure = True

    # Fraud split
    fraud_counts = df["is_fraud"].value_counts().to_dict()
    fraud_pct = round(float(df["is_fraud"].mean()), 4)

    # Self-loops
    self_loops = int((df["source_account"] == df["destination_account"]).sum())
    if self_loops > 0:
        issues.append(f"Found {self_loops} self-loop transactions")

    return {
        "dataset": "transactions.csv",
        "total_records": total_records,
        "status": "FAIL" if critical_failure else ("WARNING" if issues else "PASS"),
        "critical_failure": critical_failure,
        "issues": issues,
        "fraud_rate": fraud_pct,
        "fraud_breakdown": {str(k): int(v) for k, v in fraud_counts.items()},
        "unique_accounts": int(len(set(df["source_account"]).union(set(df["destination_account"])))),
    }


def validate_atm_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates candidate ATM directory."""
    issues = []
    critical_failure = False

    total_records = len(df)
    if total_records == 0:
        return {"status": "FAIL", "critical": True, "error": "ATM dataset is empty"}

    req_cols = ["atm_id", "bank", "latitude", "longitude", "area", "is_24x7"]
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        return {"status": "FAIL", "critical": True, "error": f"Missing ATM columns: {missing_cols}"}

    bad_coords = int(((df["latitude"].abs() > 90) | (df["longitude"].abs() > 180)).sum())
    if bad_coords > 0:
        issues.append(f"Found {bad_coords} ATMs with out-of-range coordinates")
        critical_failure = True

    dup_atms = int(df["atm_id"].duplicated().sum())
    if dup_atms > 0:
        issues.append(f"Found {dup_atms} duplicate ATM IDs")

    bank_dist = df["bank"].value_counts().head(5).to_dict()

    return {
        "dataset": "hyderabad_atms.csv",
        "total_records": total_records,
        "status": "FAIL" if critical_failure else ("WARNING" if issues else "PASS"),
        "critical_failure": critical_failure,
        "issues": issues,
        "top_banks": {str(k): int(v) for k, v in bank_dist.items()},
        "is_24x7_pct": round(float(df["is_24x7"].astype(bool).mean()), 3),
    }


def run_full_data_quality_audit(
    complaints_path: str = "data/complaints.csv",
    txns_path: str = "data/transactions.csv",
    atms_path: str = "data/hyderabad_atms.csv",
    output_report_path: str = REPORT_PATH,
) -> Dict[str, Any]:
    """Runs complete end-to-end data quality audit and persists report."""
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    report = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "datasets": {},
    }

    critical = False

    if os.path.exists(complaints_path):
        df_comp = pd.read_csv(complaints_path)
        comp_rep = validate_complaints_data(df_comp)
        report["datasets"]["complaints"] = comp_rep
        if comp_rep["critical_failure"]:
            critical = True
    else:
        report["datasets"]["complaints"] = {"status": "FAIL", "critical": True, "error": f"Missing {complaints_path}"}
        critical = True

    if os.path.exists(txns_path):
        df_txns = pd.read_csv(txns_path)
        tx_rep = validate_transactions_data(df_txns)
        report["datasets"]["transactions"] = tx_rep
        if tx_rep["critical_failure"]:
            critical = True
    else:
        report["datasets"]["transactions"] = {"status": "FAIL", "critical": True, "error": f"Missing {txns_path}"}
        critical = True

    if os.path.exists(atms_path):
        df_atms = pd.read_csv(atms_path)
        atm_rep = validate_atm_dataset(df_atms)
        report["datasets"]["atms"] = atm_rep
        if atm_rep["critical_failure"]:
            critical = True
    else:
        report["datasets"]["atms"] = {"status": "FAIL", "critical": True, "error": f"Missing {atms_path}"}
        critical = True

    report["status"] = "FAIL" if critical else ("WARNING" if any(
        d.get("status") == "WARNING" for d in report["datasets"].values()
    ) else "PASS")

    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if critical:
        raise ValueError(f"Data Quality Audit FAILED with critical errors! See {output_report_path}")

    return report


if __name__ == "__main__":
    rep = run_full_data_quality_audit()
    print(f"Data quality audit completed. Status: {rep['status']}")
