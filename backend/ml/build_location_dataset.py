"""
backend/ml/build_location_dataset.py — Project DRISHTI
========================================================
Rigorous ATM-Level Dataset Building Pipeline.

Builds a structured candidate ranking dataset where each row is:
    CASE (complaint) × CANDIDATE ATM

Labels:
    1 = Candidate was the actual cash-out ATM
    0 = Candidate was not the cash-out ATM (hard negative or spatial negative)

Dataset Type:
    "synthetic_benchmark" — explicitly designated because real-world police/banking
    withdrawal logs are proprietary and protected under RBI / DPDP Act guidelines.

Hard Negative Sampling:
    - Same-bank nearby ATMs (within 2.5 km)
    - Competing-bank nearby ATMs (within 1–4 km)
    - Same neighborhood/area terminals
    - Distant metropolitan candidates

Anti-Leakage Safeguards:
    - All historical features use ONLY transactions/withdrawals with timestamp < complaint_timestamp.
    - Preserves complaint_id grouping to prevent cross-split leakage during GroupKFold/temporal splits.

Output:
    data/synthetic_location_benchmark.csv
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from backend.ml.features import (
    FeatureEngineeringPipeline,
    haversine_distance,
    encode_bank,
    get_distance_bucket,
    calculate_as_of_historical_features,
    CITY_TIER_MAP,
)

logger = logging.getLogger(__name__)

COMPLAINTS_CSV = "data/complaints.csv"
TRANSACTIONS_CSV = "data/transactions.csv"
ATMS_CSV = "data/hyderabad_atms.csv"
POLICE_JSON = "data/police_units.json"
OUTPUT_CSV = "data/synthetic_location_benchmark.csv"
RANDOM_SEED = 42


def load_police_coords(police_json_path: str = POLICE_JSON) -> List[Tuple[float, float]]:
    """Loads police unit coordinates for distance calculation."""
    coords = []
    if os.path.exists(police_json_path):
        try:
            with open(police_json_path, "r", encoding="utf-8") as f:
                units = json.load(f)
                for u in units:
                    lat = u.get("lat", u.get("latitude"))
                    lon = u.get("lon", u.get("longitude"))
                    if lat and lon:
                        coords.append((float(lat), float(lon)))
        except Exception as e:
            logger.warning(f"Could not load police units: {e}")
    if not coords:
        coords = [(17.4156, 78.4350), (17.4399, 78.3800), (17.4435, 78.3772)]
    return coords


def min_distance_to_police(atm_lat: float, atm_lon: float, police_coords: List[Tuple[float, float]]) -> float:
    """Computes minimum distance from an ATM to nearest police patrol post."""
    dists = [haversine_distance(atm_lat, atm_lon, p_lat, p_lon) for p_lat, p_lon in police_coords]
    return float(min(dists)) if dists else 3.0


def build_location_benchmark_dataset(
    num_cases: int = 1500,
    negatives_per_case: int = 5,
    random_seed: int = RANDOM_SEED,
    output_path: str = OUTPUT_CSV,
) -> pd.DataFrame:
    """
    Generates synthetic benchmark dataset for ATM location classification/ranking.
    """
    np.random.seed(random_seed)

    if not os.path.exists(ATMS_CSV):
        raise FileNotFoundError(f"ATM catalog not found at {ATMS_CSV}")
    if not os.path.exists(COMPLAINTS_CSV):
        raise FileNotFoundError(f"Complaints dataset not found at {COMPLAINTS_CSV}")

    atms_df = pd.read_csv(ATMS_CSV)
    complaints_df = pd.read_csv(COMPLAINTS_CSV)

    police_coords = load_police_coords()

    # Precalculate ATM local densities (number of other ATMs within 1 km)
    atm_records = atms_df.to_dict(orient="records")
    atm_density_map = {}
    for atm in atm_records:
        aid = atm["atm_id"]
        alat = float(atm["latitude"])
        alon = float(atm["longitude"])
        d_count = sum(
            1 for o in atm_records
            if o["atm_id"] != aid and haversine_distance(alat, alon, float(o["latitude"]), float(o["longitude"])) <= 1.0
        )
        atm_density_map[aid] = max(1, d_count)
        atm["local_density_1km"] = atm_density_map[aid]

    # Pre-index ATMs by area and bank for realistic hard negative sampling
    area_to_atms = {}
    bank_to_atms = {}
    for atm in atm_records:
        area_to_atms.setdefault(atm.get("area", "Hyderabad"), []).append(atm)
        b_key = str(atm.get("bank", "Other")).strip()
        bank_to_atms.setdefault(b_key, []).append(atm)

    # Sort complaints chronologically to prevent temporal leakage in historical statistics
    complaints_df["dt"] = pd.to_datetime(complaints_df["timestamp"])
    complaints_df = complaints_df.sort_values("dt").reset_index(drop=True)

    # Select representative subset of complaints
    sample_complaints = complaints_df.head(num_cases).copy()

    # Create historical withdrawal registry (simulated prior withdrawal events with timestamps)
    # This acts as our as-of event log
    historical_event_log = []

    rows = []

    for idx, comp in sample_complaints.iterrows():
        cid = comp["complaint_id"]
        c_dt = comp["dt"]
        c_ts_str = comp["timestamp"]
        c_amount = float(comp["amount"])
        c_fraud_type = str(comp["fraud_type"])
        c_city = str(comp.get("city", "Hyderabad"))

        # If complaint doesn't have Hyderabad coords, map to Hyderabad bbox center for benchmark
        v_lat = float(comp["victim_lat"]) if pd.notna(comp["victim_lat"]) else 17.4150
        v_lon = float(comp["victim_lon"]) if pd.notna(comp["victim_lon"]) else 78.4350

        # If victim is outside Hyderabad bounds, center them into realistic Hyderabad corridor
        if not (17.20 <= v_lat <= 17.65 and 78.20 <= v_lon <= 78.65):
            # Deterministic offset based on complaint index
            v_lat = 17.3800 + ((idx * 7) % 200) * 0.001
            v_lon = 78.3600 + ((idx * 11) % 200) * 0.001

        comp_base = FeatureEngineeringPipeline.extract_complaint_base(
            fraud_type=c_fraud_type,
            amount=c_amount,
            complaint_dt=c_dt,
            city=c_city,
            victim_lat=v_lat,
            victim_lon=v_lon,
        )

        # Graph simulation for case
        hop_count = int(np.random.choice([2, 3, 4], p=[0.4, 0.45, 0.15]))
        trail_duration = float(np.random.uniform(12, 48))
        max_betweenness = float(np.clip(np.random.beta(0.9, 3.2), 0.01, 0.85))

        graph_metrics = {
            "hop_count": hop_count,
            "trail_duration_minutes": trail_duration,
            "mule_accounts": [f"MULE-{i}" for i in range(hop_count)],
            "max_betweenness": max_betweenness,
            "in_degree": int(np.random.randint(2, 6)),
            "out_degree": int(np.random.randint(1, 5)),
        }

        # ── 1. Select Ground Truth Positive Cash-Out ATM ─────────────────
        # Ground truth positive depends on proximity, 24x7 status for night, and bank capacity
        # Filter ATMs within 0.3 - 8.0 km
        candidates_with_dist = [
            (atm, haversine_distance(v_lat, v_lon, float(atm["latitude"]), float(atm["longitude"])))
            for atm in atm_records
        ]
        candidates_with_dist.sort(key=lambda x: x[1])

        # Pick positive from nearby ATMs (top 15 closest)
        pool_positive = [c[0] for c in candidates_with_dist[:15]]
        # Weight towards 24x7 during night and major banks
        weights = []
        is_night = comp_base["is_night"]
        for a in pool_positive:
            w = 1.0
            if is_night and a.get("is_24x7"):
                w *= 2.5
            if any(b in a.get("bank", "") for b in ["State Bank of India", "HDFC Bank", "ICICI Bank"]):
                w *= 1.8
            weights.append(w)
        weights = np.array(weights) / sum(weights)
        positive_atm = np.random.choice(pool_positive, p=weights)

        # ── 2. Select Hard Negatives ──────────────────────────────────────
        pos_lat = float(positive_atm["latitude"])
        pos_lon = float(positive_atm["longitude"])
        pos_bank = positive_atm.get("bank", "")
        pos_area = positive_atm.get("area", "")

        selected_negatives = []

        # (a) Hard negative 1: Nearby ATM (< 1.5 km) from competing bank
        nearby_competing = [
            a for a in atm_records
            if a["atm_id"] != positive_atm["atm_id"]
            and a.get("bank") != pos_bank
            and haversine_distance(pos_lat, pos_lon, float(a["latitude"]), float(a["longitude"])) <= 2.0
        ]
        if nearby_competing:
            selected_negatives.append(np.random.choice(nearby_competing))

        # (b) Hard negative 2: Same-bank ATM in nearby corridor (1.0 - 4.0 km)
        same_bank = [
            a for a in bank_to_atms.get(pos_bank, [])
            if a["atm_id"] != positive_atm["atm_id"]
            and haversine_distance(pos_lat, pos_lon, float(a["latitude"]), float(a["longitude"])) <= 4.0
        ]
        if same_bank:
            selected_negatives.append(np.random.choice(same_bank))

        # (c) Hard negative 3: Same neighborhood/area ATM
        same_area = [
            a for a in area_to_atms.get(pos_area, [])
            if a["atm_id"] != positive_atm["atm_id"]
            and a not in selected_negatives
        ]
        if same_area:
            selected_negatives.append(np.random.choice(same_area))

        # (d) Fill remaining negatives to reach negatives_per_case
        while len(selected_negatives) < negatives_per_case:
            rand_atm = np.random.choice(atm_records)
            if rand_atm["atm_id"] != positive_atm["atm_id"] and rand_atm not in selected_negatives:
                selected_negatives.append(rand_atm)

        case_candidates = [(positive_atm, 1)] + [(neg, 0) for neg in selected_negatives]

        # ── 3. Build Features for Each Candidate ──────────────────────────
        for atm, target_label in case_candidates:
            atm_id = atm["atm_id"]
            alat = float(atm["latitude"])
            alon = float(atm["longitude"])

            # Strict as-of historical feature calculation (record_ts < complaint_ts)
            hist_stats = calculate_as_of_historical_features(
                candidate_atm_id=atm_id,
                complaint_timestamp=c_dt,
                historical_withdrawals=historical_event_log,
            )

            pol_dist = min_distance_to_police(alat, alon, police_coords)

            feats = FeatureEngineeringPipeline.extract_location_candidate_features(
                complaint_base=comp_base,
                atm=atm,
                graph_metrics=graph_metrics,
                as_of_historical_stats=hist_stats,
                nearest_police_dist_km=pol_dist,
            )

            row_data = {
                "complaint_id": cid,
                "complaint_timestamp": c_ts_str,
                "atm_id": atm_id,
                "bank": atm.get("bank", "Other"),
                "area": atm.get("area", "Hyderabad"),
                "is_actual_withdrawal_location": target_label,
                "dataset_type": "synthetic_benchmark",
            }
            row_data.update(feats)
            rows.append(row_data)

        # Record positive withdrawal into historical log for FUTURE cases
        # Note: strictly registered AFTER complaint_dt + withdrawal_time
        withdrawal_event_time = c_dt + pd.Timedelta(minutes=int(np.random.uniform(20, 50)))
        historical_event_log.append({
            "atm_id": positive_atm["atm_id"],
            "timestamp": withdrawal_event_time,
            "amount": c_amount * np.random.uniform(0.75, 0.95),
            "fraud_type": c_fraud_type,
        })

    df_out = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_out.to_csv(output_path, index=False)

    logger.info(
        f"Synthetic Location Benchmark built! Rows: {len(df_out)}, "
        f"Unique cases: {df_out['complaint_id'].nunique()}, "
        f"Positives: {df_out['is_actual_withdrawal_location'].sum()}"
    )
    return df_out


if __name__ == "__main__":
    df = build_location_benchmark_dataset(num_cases=1200, negatives_per_case=5)
    print(f"Dataset generated at {OUTPUT_CSV}: {df.shape}")
