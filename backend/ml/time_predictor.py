"""
backend/ml/time_predictor.py — Project DRISHTI (Day 3)
========================================================
Inference wrapper around the trained XGBoost time-window model.

Loads the booster once at startup and exposes a clean predict() method
that the /predict endpoint can call without knowing XGBoost internals.

Usage:
    from backend.ml.time_predictor import TimeWindowPredictor
    predictor = TimeWindowPredictor()          # loads model from disk
    result = predictor.predict(
        fraud_type="upi_fraud",
        amount=25000,
        complaint_dt=datetime.now(),
        city="Mumbai"
    )
    # result.peak_minutes, result.earliest_minutes, result.latest_minutes
"""

import os
import json
import numpy as np
import xgboost as xgb
from datetime import datetime
from dataclasses import dataclass

# ─────────────────────────────────────────────
# PATHS (relative to project root)
# ─────────────────────────────────────────────
MODEL_PATH = "models/time_predictor.json"
META_PATH  = "models/feature_meta.json"


@dataclass
class TimeWindowResult:
    """Structured prediction output matching the TimeWindow Pydantic model."""
    peak_minutes:     int    # XGBoost point estimate
    earliest_minutes: int    # peak - 1 std dev (floor = 5 min)
    latest_minutes:   int    # peak + 1 std dev (ceil = 120 min)
    confidence:       float  # 0–1 confidence score derived from model internals
    features_used:    dict   # raw features fed to model (for debug/dashboard)


class TimeWindowPredictor:
    """
    Thin inference wrapper around the XGBoost withdrawal-time model.
    Thread-safe: booster.predict() is stateless after load.

    Day 4 upgrade: cache predictions per (fraud_type, amount_bucket, hour)
    tuple to avoid re-inference on identical requests in batch mode.
    """

    def __init__(self, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
        """
        Load booster + feature metadata from disk.
        Raises FileNotFoundError if model hasn't been trained yet.
        Train with: python -m backend.ml.train_xgboost
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"XGBoost model not found at '{model_path}'. "
                f"Run: python -m backend.ml.train_xgboost"
            )
        if not os.path.exists(meta_path):
            raise FileNotFoundError(
                f"Feature metadata not found at '{meta_path}'. "
                f"Run: python -m backend.ml.train_xgboost"
            )

        self._booster = xgb.Booster()
        self._booster.load_model(model_path)

        with open(meta_path, "r", encoding="utf-8") as f:
            self._meta = json.load(f)

        self._features      = self._meta.get("features", ["fraud_type_enc", "log_amount", "hour_of_day", "day_of_week", "is_weekend", "is_peak_hours", "city_tier"])
        self._fraud_map     = self._meta.get("fraud_type_map", {"upi_fraud": 0, "kyc_fraud": 1, "phishing": 2, "legitimate": 0})
        self._city_tier_map = self._meta.get("city_tier_map", {
            "Mumbai": 1, "Delhi": 1, "Bangalore": 1, "Hyderabad": 1, "Chennai": 1,
            "Kolkata": 1, "Pune": 2, "Ahmedabad": 2, "Jaipur": 2, "Lucknow": 2,
        })
        self._train_std     = self._meta.get("target_stats", {}).get("std", float(self._meta.get("rmse", 8.0)))

        # Clamp to [5, 120] minutes — the model's training range
        self._min_minutes = 5
        self._max_minutes = 120

        mae_str = self._meta.get("test_mae", self._meta.get("mae", "N/A"))
        r2_str = self._meta.get("test_r2", self._meta.get("r2", "N/A"))
        print(f"[DRISHTI] XGBoost time predictor loaded (MAE={mae_str} min, R2={r2_str})")

    def _build_feature_vector(
        self,
        fraud_type:   str,
        amount:       float,
        complaint_dt: datetime,
        city:         str,
    ) -> tuple[list[float], dict]:
        """
        Encode raw inputs into the feature vector expected by the booster.
        Returns (feature_list, feature_dict_for_debug).
        """
        fraud_enc    = self._fraud_map.get(fraud_type, 0)
        log_amount   = float(np.log1p(max(amount, 0)))
        hour         = complaint_dt.hour
        dow          = complaint_dt.weekday()    # 0=Mon
        is_weekend   = int(dow >= 5)
        is_peak      = int(18 <= hour <= 22)
        city_tier    = self._city_tier_map.get(city, 2)

        vec = [fraud_enc, log_amount, hour, dow, is_weekend, is_peak, city_tier]
        dbg = dict(zip(self._features, vec))
        return vec, dbg

    def predict(
        self,
        fraud_type:   str,
        amount:       float,
        complaint_dt: datetime = None,
        city:         str = "Unknown",
    ) -> TimeWindowResult:
        """
        Predict withdrawal time window for one complaint.

        Args:
            fraud_type:   "upi_fraud" | "kyc_fraud" | "phishing"
            amount:       Fraud amount in INR
            complaint_dt: Datetime of complaint (defaults to now)
            city:         City name (for tier lookup)

        Returns:
            TimeWindowResult with peak / earliest / latest / confidence
        """
        if complaint_dt is None:
            complaint_dt = datetime.utcnow()

        vec, dbg = self._build_feature_vector(fraud_type, amount, complaint_dt, city)

        dm   = xgb.DMatrix([vec], feature_names=self._features)
        raw  = float(self._booster.predict(dm)[0])
        peak = int(np.clip(round(raw), self._min_minutes, self._max_minutes))

        # Build ±1σ interval around point estimate
        # Use model's training std dev as a proxy for prediction uncertainty.
        # Day 4: replace with quantile regression (XGBoost supports it natively)
        sigma      = self._train_std * 0.6   # ×0.6 because model explains some variance
        earliest   = int(max(self._min_minutes, round(peak - sigma)))
        latest     = int(min(self._max_minutes, round(peak + sigma)))

        # Confidence: higher when peak is far from the 5/120 boundary
        #             lower when clamped (model is extrapolating)
        boundary_proximity = min(peak - self._min_minutes,
                                 self._max_minutes - peak) / self._max_minutes
        confidence = round(min(0.95, max(0.4, 0.55 + boundary_proximity * 0.5)), 3)

        return TimeWindowResult(
            peak_minutes=peak,
            earliest_minutes=earliest,
            latest_minutes=latest,
            confidence=confidence,
            features_used=dbg,
        )

    @property
    def is_loaded(self) -> bool:
        return self._booster is not None

    @property
    def model_meta(self) -> dict:
        return self._meta


# ─────────────────────────────────────────────
# Quick self-test when run directly
# ─────────────────────────────────────────────
if __name__ == "__main__":
    predictor = TimeWindowPredictor()
    cases = [
        ("upi_fraud",  25000, datetime(2026, 9, 1, 20, 0), "Mumbai"),
        ("kyc_fraud",  100000, datetime(2026, 9, 1, 10, 0), "Jaipur"),
        ("phishing",   5000,  datetime(2026, 9, 6, 14, 0), "Delhi"),
        ("upi_fraud",  500,   datetime(2026, 9, 7, 21, 0), "Lucknow"),
    ]
    print("\n--- TimeWindowPredictor self-test ---")
    for ft, amt, dt, city in cases:
        r = predictor.predict(ft, amt, dt, city)
        print(f"  {ft:<12} Rs{amt:>7,}  {city:<10}  "
              f"peak={r.peak_minutes:>3}min  "
              f"window=[{r.earliest_minutes},{r.latest_minutes}]  "
              f"conf={r.confidence:.0%}")
