"""
Transaction Dataset Quality & Integrity Validator
Verifies data/transactions.csv against strict schema, statistical and relational constraints.
"""

import os
import sys
import pandas as pd
import numpy as np


def validate_transactions(csv_path: str = "data/transactions.csv") -> dict:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)
    total_records = len(df)
    if total_records < 2000:
        raise ValueError(f"Insufficient records: {total_records} (minimum 2000 required)")

    # Required columns
    required_cols = [
        "transaction_id",
        "source_account",
        "destination_account",
        "amount",
        "timestamp",
        "transaction_type",
        "fraud_type",
        "source_latitude",
        "source_longitude",
        "destination_latitude",
        "destination_longitude",
        "source_bank",
        "destination_bank",
        "device_id",
        "ip_risk_score",
        "is_fraud",
        "hop_number",
        "commission_amount",
    ]

    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # 1. No missing IDs
    assert df["transaction_id"].notna().all(), "Missing transaction_id found"
    assert df["source_account"].notna().all(), "Missing source_account found"
    assert df["destination_account"].notna().all(), "Missing destination_account found"

    # 2. No duplicate transaction IDs
    assert df["transaction_id"].is_unique, "Duplicate transaction_id values found"

    # 3. No negative transaction amounts
    assert (df["amount"] > 0).all(), "Negative or zero amount values found"

    # 4. No malformed timestamps
    try:
        timestamps = pd.to_datetime(df["timestamp"])
        assert timestamps.notna().all(), "Malformed timestamps found"
    except Exception as e:
        raise AssertionError(f"Timestamp parsing error: {e}")

    # 5. Valid latitude/longitude ranges
    for lat_col in ["source_latitude", "destination_latitude"]:
        assert df[lat_col].between(-90.0, 90.0).all(), f"Invalid {lat_col} values out of range"
    for lon_col in ["source_longitude", "destination_longitude"]:
        assert df[lon_col].between(-180.0, 180.0).all(), f"Invalid {lon_col} values out of range"

    # 6. Valid fraud labels
    assert set(df["is_fraud"].unique()).issubset({0, 1}), "Invalid is_fraud values"

    # 7. Valid hop numbers (0 for direct non-fraud retail transfer, >= 1 for fraud chains)
    assert (df["hop_number"] >= 0).all(), "Negative hop_number found"
    assert (df.loc[df["is_fraud"] == 1, "hop_number"] >= 1).all(), "Fraud records must have hop_number >= 1"

    # 8. Valid source != destination
    assert (df["source_account"] != df["destination_account"]).all(), "Self-transfers found"

    # Relational pattern calculations
    unique_accounts = len(set(df["source_account"]).union(set(df["destination_account"])))
    fraud_records = int((df["is_fraud"] == 1).sum())
    normal_records = int((df["is_fraud"] == 0).sum())
    multihop_chains = int((df["hop_number"] > 1).sum())

    # Fan-in patterns: destinations receiving from >= 3 distinct sources
    in_counts = df.groupby("destination_account")["source_account"].nunique()
    fan_in_count = int((in_counts >= 3).sum())

    # Fan-out patterns: sources sending to >= 3 distinct destinations
    out_counts = df.groupby("source_account")["destination_account"].nunique()
    fan_out_count = int((out_counts >= 3).sum())

    report = {
        "status": "PASS",
        "records": total_records,
        "unique_transactions": len(df["transaction_id"].unique()),
        "fraud_records": fraud_records,
        "normal_records": normal_records,
        "unique_accounts": unique_accounts,
        "multihop_chains": multihop_chains,
        "fan_in_patterns": fan_in_count,
        "fan_out_patterns": fan_out_count,
        "amount_min": float(df["amount"].min()),
        "amount_max": float(df["amount"].max()),
        "amount_mean": float(round(df["amount"].mean(), 2)),
        "amount_median": float(round(df["amount"].median(), 2)),
    }

    return report


if __name__ == "__main__":
    report = validate_transactions()
    print("Dataset validation: PASS")
    print(f"Records: {report['records']}")
    print(f"Unique transactions: {report['unique_transactions']}")
    print(f"Fraud records: {report['fraud_records']}")
    print(f"Normal records: {report['normal_records']}")
    print(f"Unique accounts: {report['unique_accounts']}")
    print(f"Multi-hop chains: {report['multihop_chains']}")
    print(f"Fan-in patterns: {report['fan_in_patterns']}")
    print(f"Fan-out patterns: {report['fan_out_patterns']}")
    print(f"Amount distribution: min=Rs {report['amount_min']}, median=Rs {report['amount_median']}, mean=Rs {report['amount_mean']}, max=Rs {report['amount_max']}")
    sys.exit(0)
