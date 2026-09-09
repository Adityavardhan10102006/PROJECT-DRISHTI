"""
backend/domain/prediction.py — Project DRISHTI
==============================================
Encapsulates prediction domain value objects:
RiskPrediction, AmountPrediction, TimePrediction, and generic PredictionResult.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class PredictionResult:
    """Base domain value object for model outputs."""
    prediction: Any = None
    model_source: str = "trained_ml"
    confidence: float = 0.85
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": self.prediction,
            "model_source": self.model_source,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class RiskPrediction(PredictionResult):
    """Encapsulates AI/ML risk classification and SHAP attribution results."""
    risk_score: float = 50.0
    risk_level: str = "MEDIUM"
    probabilities: Dict[str, float] = field(default_factory=dict)
    key_factors: List[Dict[str, Any]] = field(default_factory=list)
    top_positive_features: List[Dict[str, Any]] = field(default_factory=list)
    top_negative_features: List[Dict[str, Any]] = field(default_factory=list)
    shap_available: bool = False

    def is_critical(self) -> bool:
        return self.risk_level in ("HIGH", "CRITICAL") or self.risk_score >= 70.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "probabilities": self.probabilities,
            "key_factors": self.key_factors,
            "top_positive_features": self.top_positive_features,
            "top_negative_features": self.top_negative_features,
            "shap_available": self.shap_available,
        })
        return base


@dataclass
class AmountPrediction(PredictionResult):
    """Encapsulates learned cash-out amount regression with prediction intervals."""
    predicted_cashout_amount: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    mae: float = 1942.97

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "predicted_cashout_amount": self.predicted_cashout_amount,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "mae": self.mae,
        })
        return base


@dataclass
class TimePrediction(PredictionResult):
    """Encapsulates XGBoost withdrawal time-window regression with conformal intervals."""
    earliest_minutes: int = 5
    latest_minutes: int = 60
    peak_minutes: int = 35
    conformal_q_90: float = 10.6

    @property
    def window_span(self) -> int:
        return max(0, self.latest_minutes - self.earliest_minutes)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "earliest_minutes": self.earliest_minutes,
            "latest_minutes": self.latest_minutes,
            "peak_minutes": self.peak_minutes,
            "conformal_q_90": self.conformal_q_90,
            "window_span": self.window_span,
        })
        return base
