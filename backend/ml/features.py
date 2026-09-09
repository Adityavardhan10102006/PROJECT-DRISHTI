"""
backend/ml/features.py — Project DRISHTI
==========================================
Unified Feature Engineering & Pipeline Engine.

Guarantees identical feature transformations across training and inference.
Enforces strict anti-leakage principles:
  - Temporal "as-of" historical lookups: historical observations must strictly
    predate the complaint incident timestamp (record_ts < complaint_ts).
  - Consistent categorical mapping and scaling.
  - Generates models/feature_schema.json for schema contract enforcement.
"""

import os
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

FRAUD_TYPE_MAP = {
    "upi_fraud": 0,
    "kyc_fraud": 1,
    "phishing": 2,
    "legitimate": 3,
}

BANK_MAP = {
    "State Bank of India": 0,
    "HDFC Bank": 1,
    "ICICI Bank": 2,
    "Axis Bank": 3,
    "Kotak Mahindra Bank": 4,
    "Punjab National Bank": 5,
    "Bank of Baroda": 6,
    "Canara Bank": 7,
    "Union Bank of India": 8,
    "Other": 9,
}

CITY_TIER_MAP = {
    "Mumbai": 1, "Delhi": 1, "Bangalore": 1, "Hyderabad": 1, "Chennai": 1, "Kolkata": 1,
    "Pune": 2, "Ahmedabad": 2, "Jaipur": 2, "Lucknow": 2,
    "Unknown": 2,
}

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Exact Haversine distance in kilometers."""
    try:
        r = math.radians
        dlat = r(lat2 - lat1)
        dlon = r(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(dlon / 2) ** 2
        return float(EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
    except Exception:
        return 999.0


def encode_bank(bank_name: Optional[str]) -> int:
    """Encodes bank name using canonical mapping."""
    if not bank_name:
        return BANK_MAP["Other"]
    for b, code in BANK_MAP.items():
        if b.lower() in str(bank_name).lower():
            return code
    return BANK_MAP["Other"]


def get_distance_bucket(dist_km: float) -> int:
    """Discretizes distance into operational buckets: 0: <1km, 1: 1-3km, 2: 3-5km, 3: 5-10km, 4: >10km."""
    if dist_km < 1.0:
        return 0
    elif dist_km < 3.0:
        return 1
    elif dist_km < 5.0:
        return 2
    elif dist_km < 10.0:
        return 3
    return 4


class FeatureEngineeringPipeline:
    """
    Centralized Feature Engineering for Location, Time, Amount, and Risk models.
    """

    LOCATION_FEATURE_NAMES = [
        # Geographic
        "distance_km",
        "distance_bucket",
        "atm_latitude",
        "atm_longitude",
        "victim_latitude",
        "victim_longitude",
        # ATM characteristics
        "bank_enc",
        "is_24x7",
        "local_density_1km",
        "dist_to_police_km",
        # Complaint context
        "fraud_type_enc",
        "amount",
        "log_amount",
        "complaint_hour",
        "day_of_week",
        "is_weekend",
        "is_night",
        "city_tier",
        # Money trail / network
        "hop_count",
        "trail_duration_mins",
        "mule_count",
        "max_betweenness",
        "in_degree",
        "out_degree",
        # Historical as-of spatial features
        "hist_atm_withdrawals",
        "hist_atm_cashout_sum",
        "hist_tod_match",
    ]

    TIME_FEATURE_NAMES = [
        "fraud_type_enc",
        "log_amount",
        "hour_of_day",
        "day_of_week",
        "is_weekend",
        "is_peak_hours",
        "city_tier",
        "hop_count",
        "trail_duration_mins",
        "velocity_mins",
        "max_betweenness",
    ]

    AMOUNT_FEATURE_NAMES = [
        "fraud_type_enc",
        "initial_amount",
        "log_amount",
        "hop_count",
        "velocity_mins",
        "commission_rate",
        "hour",
        "day_of_week",
        "city_tier",
    ]

    RISK_FEATURE_NAMES = [
        "fraud_type_enc",
        "log_amount",
        "hop_count",
        "betweenness_centrality",
        "in_degree",
        "out_degree",
        "hour",
        "is_weekend",
        "city_tier",
        "est_withdrawal_mins",
    ]

    @staticmethod
    def extract_complaint_base(
        fraud_type: str,
        amount: float,
        complaint_dt: datetime,
        city: str = "Unknown",
        victim_lat: Optional[float] = None,
        victim_lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Extracts standard complaint base attributes."""
        dt = complaint_dt if complaint_dt is not None else datetime.now(timezone.utc)
        hour = dt.hour
        dow = dt.weekday()
        is_wknd = int(dow >= 5)
        is_ngt = int(hour >= 20 or hour <= 6)
        ft_enc = FRAUD_TYPE_MAP.get(str(fraud_type).lower(), 0)
        safe_amt = max(float(amount or 0.0), 0.0)
        log_amt = float(np.log1p(safe_amt))
        c_tier = CITY_TIER_MAP.get(city, 2)

        return {
            "fraud_type_enc": ft_enc,
            "amount": safe_amt,
            "log_amount": log_amt,
            "complaint_hour": hour,
            "day_of_week": dow,
            "is_weekend": is_wknd,
            "is_night": is_ngt,
            "city_tier": c_tier,
            "victim_latitude": float(victim_lat) if victim_lat is not None else 0.0,
            "victim_longitude": float(victim_lon) if victim_lon is not None else 0.0,
        }

    @staticmethod
    def extract_location_candidate_features(
        complaint_base: Dict[str, Any],
        atm: Dict[str, Any],
        graph_metrics: Optional[Dict[str, Any]] = None,
        as_of_historical_stats: Optional[Dict[str, Any]] = None,
        nearest_police_dist_km: float = 2.5,
    ) -> Dict[str, float]:
        """
        Builds feature dictionary for one (Case, Candidate ATM) pair.
        Strictly zero data leakage: uses as_of_historical_stats calculated prior to complaint_ts.
        """
        gm = graph_metrics or {}
        ah = as_of_historical_stats or {}

        v_lat = complaint_base.get("victim_latitude", 0.0)
        v_lon = complaint_base.get("victim_longitude", 0.0)
        atm_lat = float(atm.get("latitude", atm.get("lat", 0.0)))
        atm_lon = float(atm.get("longitude", atm.get("lon", 0.0)))

        dist_km = haversine_distance(v_lat, v_lon, atm_lat, atm_lon) if (v_lat and v_lon) else 1.5
        dist_bucket = get_distance_bucket(dist_km)

        bank_name = atm.get("bank", "Other")
        bank_enc = encode_bank(bank_name)
        is_24x7 = 1.0 if atm.get("is_24x7", True) in [True, 1, "True", "true"] else 0.0
        local_density = float(atm.get("local_density_1km", atm.get("atm_count", 1)))

        hour = complaint_base.get("complaint_hour", 14)

        return {
            "distance_km": float(dist_km),
            "distance_bucket": float(dist_bucket),
            "atm_latitude": float(atm_lat),
            "atm_longitude": float(atm_lon),
            "victim_latitude": float(v_lat),
            "victim_longitude": float(v_lon),
            "bank_enc": float(bank_enc),
            "is_24x7": float(is_24x7),
            "local_density_1km": float(local_density),
            "dist_to_police_km": float(nearest_police_dist_km),
            "fraud_type_enc": float(complaint_base.get("fraud_type_enc", 0)),
            "amount": float(complaint_base.get("amount", 0.0)),
            "log_amount": float(complaint_base.get("log_amount", 0.0)),
            "complaint_hour": float(hour),
            "day_of_week": float(complaint_base.get("day_of_week", 2)),
            "is_weekend": float(complaint_base.get("is_weekend", 0)),
            "is_night": float(complaint_base.get("is_night", 0)),
            "city_tier": float(complaint_base.get("city_tier", 1)),
            "hop_count": float(gm.get("hop_count", 2)),
            "trail_duration_mins": float(gm.get("trail_duration_minutes", 25.0)),
            "mule_count": float(len(gm.get("mule_accounts", [])) or 2),
            "max_betweenness": float(gm.get("max_betweenness", 0.05)),
            "in_degree": float(gm.get("in_degree", 2)),
            "out_degree": float(gm.get("out_degree", 2)),
            # Historical features strictly as of complaint timestamp
            "hist_atm_withdrawals": float(ah.get("withdrawal_count", 0)),
            "hist_atm_cashout_sum": float(ah.get("cashout_sum", 0.0)),
            "hist_tod_match": float(ah.get("tod_match", 0.5)),
        }

    @classmethod
    def get_feature_schema(cls) -> Dict[str, Any]:
        """Builds standardized feature schema definition."""
        return {
            "schema_version": "1.0.0",
            "models": {
                "location_model": {
                    "feature_names": cls.LOCATION_FEATURE_NAMES,
                    "target": "is_actual_withdrawal_location (0 or 1)",
                    "group_key": "complaint_id",
                    "leakage_controls": [
                        "Candidate rows grouped by complaint_id",
                        "Historical ATM statistics computed with strict t < complaint_timestamp constraint",
                        "Future withdrawals excluded from candidate evaluation",
                    ],
                },
                "time_model": {
                    "feature_names": cls.TIME_FEATURE_NAMES,
                    "target": "withdrawal_minutes (positive float)",
                    "leakage_controls": [
                        "Chronological temporal split (earlier 70%, mid 15%, latest 15%)",
                        "Conformal calibration performed exclusively on validation partition",
                    ],
                },
                "amount_model": {
                    "feature_names": cls.AMOUNT_FEATURE_NAMES,
                    "target": "final_cashout_amount (positive float)",
                    "leakage_controls": [
                        "Realistic non-deterministic target incorporating partial cashouts and ATM limits",
                        "No direct algebraic mapping from input features",
                    ],
                },
                "risk_model": {
                    "feature_names": cls.RISK_FEATURE_NAMES,
                    "target": "risk_tier (0: LOW, 1: MEDIUM, 2: HIGH, 3: CRITICAL)",
                    "leakage_controls": [
                        "Stratified holdout validation",
                        "Calibrated probability scaling (Isotonic/Platt)",
                    ],
                },
            },
        }

    @classmethod
    def save_feature_schema(cls, output_path: str = "models/feature_schema.json"):
        """Saves feature schema JSON to disk."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        schema = cls.get_feature_schema()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
        return schema


def calculate_as_of_historical_features(
    candidate_atm_id: str,
    complaint_timestamp: datetime,
    historical_withdrawals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    CRITICAL ANTI-LEAKAGE FUNCTION:
    Computes ATM historical features strictly using events that occurred BEFORE complaint_timestamp.
    Never includes equal or future timestamps.
    """
    count = 0
    cashout_sum = 0.0
    tod_matches = 0
    target_hour = complaint_timestamp.hour

    for event in historical_withdrawals:
        if event.get("atm_id") != candidate_atm_id:
            continue
        event_ts = event.get("timestamp")
        if isinstance(event_ts, str):
            try:
                event_dt = datetime.fromisoformat(event_ts.replace("Z", "+00:00"))
            except Exception:
                continue
        elif isinstance(event_ts, datetime):
            event_dt = event_ts
        else:
            continue

        # Strict anti-leakage inequality: must be strictly earlier
        if event_dt >= complaint_timestamp:
            continue

        count += 1
        cashout_sum += float(event.get("amount", 0.0))
        if abs(event_dt.hour - target_hour) <= 3:
            tod_matches += 1

    tod_match_rate = (tod_matches / count) if count > 0 else 0.5

    return {
        "withdrawal_count": count,
        "cashout_sum": cashout_sum,
        "tod_match": tod_match_rate,
    }


if __name__ == "__main__":
    FeatureEngineeringPipeline.save_feature_schema()
    print("Feature schema successfully generated.")
