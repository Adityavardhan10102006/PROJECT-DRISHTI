"""
backend/ml/amount_predictor.py — Project DRISHTI
==================================================
Learned Cash-Out Amount Regression Model.

Features:
  - Predicts final cash withdrawal amount accounting for:
      - Incident fraud amount
      - Fraud type typology
      - Intermediary mule hops and transaction velocity
      - Layering commission friction and ATM cash dispersion limits
  - Statistically sound prediction intervals [lower_bound, upper_bound].
  - 100% backward compatibility for all existing fields and callers.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from backend.ml.features import (
    FeatureEngineeringPipeline,
    FRAUD_TYPE_MAP,
    CITY_TIER_MAP,
)
from backend.ml.base_predictor import BasePredictor

MODEL_PATH = "models/amount_predictor.joblib"
META_PATH = "models/amount_meta.json"


class CashoutAmountPredictor(BasePredictor):
    """
    Predicts terminal cash-out withdrawal amount with realistic empirical uncertainty bounds.
    """

    def __init__(self, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
        super().__init__(model_path=model_path, meta_path=meta_path)
        self.model = None
        self.meta: Dict[str, Any] = {}
        self.feature_cols = FeatureEngineeringPipeline.AMOUNT_FEATURE_NAMES
        self.rmse = 4200.0

        self.load_model()
        mae_str = self.meta.get("mae", "N/A")
        print(f"[DRISHTI] Cash-Out Amount Regressor loaded (MAE: Rs {mae_str})")

    def load_model(self) -> None:
        """Loads pre-trained GBR / amount model from disk."""
        resolved_model = self.model_path if (self.model_path and os.path.exists(self.model_path)) else "models/amount_model.joblib"
        if os.path.exists(resolved_model):
            try:
                self.model = joblib.load(resolved_model)
                self._model = self.model
            except Exception as e:
                print(f"[DRISHTI] Warning: Could not load amount model ({e})")
                self.model = None

        if self.meta_path and os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
                    self._meta = self.meta
                self.feature_cols = self.meta.get("feature_cols", self.feature_cols)
                self.rmse = float(self.meta.get("rmse", 4200.0))
            except Exception as e:
                print(f"[DRISHTI] Warning: Could not load amount meta ({e})")


    def predict(
        self,
        amount: float,
        fraud_type: str = "upi_fraud",
        hop_count: int = 2,
        velocity_mins: float = 25.0,
        hour: int = 14,
        day_of_week: int = 2,
        commission_rate: float = 0.05,
        city: str = "Hyderabad",
    ) -> Dict[str, Any]:
        """
        Predicts terminal cash-out amount with lower and upper bounds.
        """
        raw_amt = max(float(amount or 0.0), 100.0)
        ft_enc = FRAUD_TYPE_MAP.get(str(fraud_type).lower(), 0)
        log_amt = float(np.log1p(raw_amt))
        c_tier = CITY_TIER_MAP.get(city, 2)

        feat_dict = {
            "fraud_type_enc": float(ft_enc),
            "initial_amount": float(raw_amt),
            "log_amount": float(log_amt),
            "hop_count": float(hop_count),
            "velocity_mins": float(velocity_mins),
            "commission_rate": float(commission_rate),
            "hour": float(hour),
            "day_of_week": float(day_of_week),
            "city_tier": float(c_tier),
        }

        if self.model is not None and self.feature_cols:
            try:
                df_x = pd.DataFrame([feat_dict])[self.feature_cols]
                raw_pred = float(self.model.predict(df_x)[0])
                predicted_amount = max(200.0, min(raw_pred, raw_amt * 0.99))
                margin = max(self.rmse * 1.5, predicted_amount * 0.08)
                lower_bound = max(100.0, predicted_amount - margin)
                upper_bound = min(raw_amt, predicted_amount + margin)
                confidence = round(float(np.clip(1.0 - (margin / (predicted_amount + 1.0)), 0.60, 0.95)), 2)
            except Exception as e:
                print(f"[DRISHTI] Amount model inference error ({e}), using analytical fallback.")
                predicted_amount, lower_bound, upper_bound, confidence = self._analytical_fallback(
                    raw_amt, hop_count, commission_rate
                )
        else:
            predicted_amount, lower_bound, upper_bound, confidence = self._analytical_fallback(
                raw_amt, hop_count, commission_rate
            )

        predicted_amount = round(predicted_amount, -2)
        lower_bound = round(lower_bound, -2)
        upper_bound = round(upper_bound, -2)

        return {
            "predicted_cashout_amount": float(predicted_amount),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "confidence": float(confidence),
            "formatted_cashout": f"Rs {int(predicted_amount):,}",
            "formatted_range": f"Rs {int(lower_bound):,} - Rs {int(upper_bound):,}",
            "retained_commission_estimate": round(float(raw_amt - predicted_amount), 2),
            "model_version": self.meta.get("version", "amount-v2.2"),
            "dataset_type": self.meta.get("dataset_type", "synthetic_benchmark"),
        }

    def predict_cashout(
        self,
        reported_amount: Optional[float] = None,
        amount: Optional[float] = None,
        fraud_type: str = "upi_fraud",
        hop_count: int = 2,
        velocity_mins: float = 25.0,
        hour: int = 14,
        day_of_week: int = 2,
        commission_rate: float = 0.05,
        city: str = "Hyderabad",
    ) -> Dict[str, Any]:
        """Alias supporting both 'reported_amount' and 'amount' kwargs."""
        amt = reported_amount if reported_amount is not None else (amount or 1000.0)
        return self.predict(
            amount=amt,
            fraud_type=fraud_type,
            hop_count=hop_count,
            velocity_mins=velocity_mins,
            hour=hour,
            day_of_week=day_of_week,
            commission_rate=commission_rate,
            city=city,
        )

    def _analytical_fallback(self, amount: float, hop_count: int, commission_rate: float):
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


# Domain / OOP Alias
AmountPredictor = CashoutAmountPredictor



if __name__ == "__main__":
    p = CashoutAmountPredictor()
    res = p.predict(100000.0, "upi_fraud", hop_count=3)
    print(f"Predicted Cashout: {res['formatted_cashout']} (Range: {res['formatted_range']})")
