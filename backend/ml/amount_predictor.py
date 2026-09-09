"""
backend/ml/amount_predictor.py — Project DRISHTI
==================================================
Learned Cash-Out Amount Regression Model.

Replaces static rule deductions with a trained machine learning model
(GradientBoostingRegressor) predicting the final cash withdrawal amount,
accounting for:
  - Incident fraud amount
  - Fraud type (UPI, KYC, Phishing)
  - Number of intermediary mule hops
  - Transaction velocity (latency in minutes)
  - Layering commission erosion
  - Temporal patterns (hour, day of week)

Outputs:
  - predicted_cashout_amount (float)
  - lower_bound (float)
  - upper_bound (float)
  - confidence (float: 0.0 to 1.0)
  - formatted_summary (str)
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

MODEL_PATH = "models/amount_predictor.joblib"
META_PATH = "models/amount_meta.json"

FRAUD_TYPE_MAP = {"upi_fraud": 0, "kyc_fraud": 1, "phishing": 2, "legitimate": 0}


class CashoutAmountPredictor:
    """
    Predicts the expected cash-out withdrawal amount and realistic confidence bounds.
    """

    def __init__(self, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
        self.model = None
        self.meta = {}
        self.feature_cols = []
        self.rmse = 4500.0

        if os.path.exists(model_path) and os.path.exists(meta_path):
            try:
                self.model = joblib.load(model_path)
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
                self.feature_cols = self.meta.get("feature_cols", [])
                self.rmse = float(self.meta.get("rmse", 4500.0))
                print(f"[DRISHTI] Cash-Out Amount Regressor loaded (MAE: Rs {self.meta.get('mae', 'N/A')})")
            except Exception as e:
                print(f"[DRISHTI] Warning: Could not load amount model ({e}), using fallback.")
                self.model = None

    def predict(
        self,
        amount: float,
        fraud_type: str = "upi_fraud",
        hop_count: int = 2,
        velocity_mins: float = 25.0,
        hour: int = 14,
        day_of_week: int = 2,
        commission_rate: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Predicts terminal cash-out amount with lower and upper bounds.
        """
        amount = max(float(amount), 100.0)
        ft_enc = FRAUD_TYPE_MAP.get(fraud_type.lower(), 0)
        log_amt = float(np.log1p(amount))

        features = {
            "fraud_type_enc": float(ft_enc),
            "initial_amount": float(amount),
            "log_amount": log_amt,
            "hop_count": float(hop_count),
            "velocity_mins": float(velocity_mins),
            "commission_rate": float(commission_rate),
            "hour": float(hour),
            "day_of_week": float(day_of_week),
        }

        if self.model is not None and self.feature_cols:
            try:
                df_x = pd.DataFrame([features])[self.feature_cols]
                raw_pred = float(self.model.predict(df_x)[0])
                predicted_amount = max(500.0, min(raw_pred, amount * 0.99))
                # Confidence intervals based on empirical test RMSE
                margin = max(self.rmse * 1.2, predicted_amount * 0.08)
                lower_bound = max(100.0, predicted_amount - margin)
                upper_bound = min(amount, predicted_amount + margin)
                confidence = round(float(np.clip(1.0 - (margin / (predicted_amount + 1.0)), 0.60, 0.95)), 2)
            except Exception as e:
                print(f"[DRISHTI] Amount model inference error ({e}), using analytical fallback.")
                predicted_amount, lower_bound, upper_bound, confidence = self._analytical_fallback(
                    amount, hop_count, commission_rate
                )
        else:
            predicted_amount, lower_bound, upper_bound, confidence = self._analytical_fallback(
                amount, hop_count, commission_rate
            )

        predicted_amount = round(predicted_amount, -2) # Round to nearest 100 for realistic cashout
        lower_bound = round(lower_bound, -2)
        upper_bound = round(upper_bound, -2)

        return {
            "predicted_cashout_amount": float(predicted_amount),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "confidence": float(confidence),
            "formatted_cashout": f"₹{int(predicted_amount):,}",
            "formatted_range": f"₹{int(lower_bound):,} – ₹{int(upper_bound):,}",
            "retained_commission_estimate": round(float(amount - predicted_amount), 2),
        }

    def _analytical_fallback(
        self, amount: float, hop_count: int, commission_rate: float
    ):
        # Default ~4.5% cut per intermediary hop
        effective_hops = max(hop_count - 1, 1)
        rate = commission_rate if commission_rate > 0 else 0.045
        retained = amount * (1.0 - (rate * effective_hops))
        predicted = max(200.0, min(retained, amount * 0.96))
        margin = predicted * 0.08
        return predicted, predicted - margin, min(amount, predicted + margin), 0.78


_amount_predictor_instance: Optional[CashoutAmountPredictor] = None

def get_amount_predictor() -> CashoutAmountPredictor:
    global _amount_predictor_instance
    if _amount_predictor_instance is None:
        _amount_predictor_instance = CashoutAmountPredictor()
    return _amount_predictor_instance
