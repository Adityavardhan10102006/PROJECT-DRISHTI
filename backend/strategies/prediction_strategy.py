"""
backend/strategies/prediction_strategy.py — Project DRISHTI
============================================================
Polymorphic strategy pattern for ML vs Heuristic fallback execution.
Clearly distinguishes between trained ML predictions and domain heuristics.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional, List
from backend.domain.prediction import PredictionResult


class PredictionStrategy(ABC):
    """
    Abstract Strategy for inference execution.
    Demonstrates Polymorphism across ML models and heuristic fallbacks.
    """

    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> PredictionResult:
        """Executes prediction for the given features."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Returns 'trained_ml' or 'heuristic_fallback'."""
        pass


class MLPredictionStrategy(PredictionStrategy):
    """
    Strategy delegating inference to an active, trained ML model.
    """

    def __init__(
        self,
        inference_fn: Optional[Callable[[Dict[str, Any]], Any]] = None,
        model: Optional[Any] = None,
        feature_names: Optional[List[str]] = None,
        model_name: str = "ml_model",
    ):
        self._inference_fn = inference_fn
        self.model = model
        self.feature_names = feature_names or []
        self.model_name = model_name

    @property
    def source_name(self) -> str:
        return "trained_ml"

    def predict(self, features: Dict[str, Any]) -> PredictionResult:
        if self._inference_fn:
            res = self._inference_fn(features)
        elif self.model and hasattr(self.model, "predict"):
            import numpy as np
            row = [features.get(k, 0.0) for k in (self.feature_names or features.keys())]
            pred = self.model.predict(np.array([row]))
            res = {"prediction": pred[0] if len(pred) > 0 else 0.0}
        else:
            res = {"prediction": 0.0}

        val = res.get("prediction", res) if isinstance(res, dict) else res
        return PredictionResult(
            prediction=val,
            model_source=self.source_name,
            confidence=float(res.get("confidence", 0.85)) if isinstance(res, dict) else 0.85,
            metadata=res if isinstance(res, dict) else {"raw": res},
        )


class HeuristicPredictionStrategy(PredictionStrategy):
    """
    Rule-based fallback strategy used when ML model is unavailable or input is out-of-distribution.
    """

    def __init__(
        self,
        fallback_fn: Optional[Callable[[Dict[str, Any]], Any]] = None,
        default_prediction: Optional[Any] = None,
    ):
        self._fallback_fn = fallback_fn
        self.default_prediction = default_prediction

    @property
    def source_name(self) -> str:
        return "heuristic_fallback"

    def predict(self, features: Dict[str, Any]) -> PredictionResult:
        if self._fallback_fn:
            res = self._fallback_fn(features)
        else:
            res = {"prediction": self.default_prediction}

        val = res.get("prediction", res) if isinstance(res, dict) else res
        return PredictionResult(
            prediction=val,
            model_source=self.source_name,
            confidence=0.5,
            metadata=res if isinstance(res, dict) else {"raw": res},
        )
