"""
backend/ml/base_predictor.py — Project DRISHTI
==============================================
Abstract Base Class and Factory for Machine Learning predictors.
Demonstrates Abstraction, Inheritance, and Polymorphism.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePredictor(ABC):
    """
    Abstract Base Class for all ML & statistical predictors in Project DRISHTI.

    Abstraction:
      - Defines a standard unified interface across Risk, Amount, and Time predictors.
    """

    def __init__(self, model_path: Optional[str] = None, meta_path: Optional[str] = None):
        self.model_path = model_path
        self.meta_path = meta_path
        self._model = None
        self._meta: Dict[str, Any] = {}

    @abstractmethod
    def load_model(self) -> None:
        """Loads pre-trained weights/artifacts from disk."""
        pass

    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> Any:
        """Executes inference and returns structured domain result."""
        pass

    @property
    def is_loaded(self) -> bool:
        """Checks if underlying model artifact is loaded."""
        return self._model is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns model evaluation metrics and training provenance."""
        return dict(self._meta)


class PredictorFactory:
    """
    Factory Pattern for instantiating predictors by typology.
    Reduces coupling between caller and concrete ML model classes.
    """

    @staticmethod
    def create_predictor(model_type: str) -> BasePredictor:
        typ = str(model_type).strip().lower()
        if typ in ("risk", "case_risk", "classifier"):
            from backend.ml.risk_predictor import get_risk_predictor
            return get_risk_predictor()
        elif typ in ("amount", "cashout", "cashout_amount"):
            from backend.ml.amount_predictor import get_amount_predictor
            return get_amount_predictor()
        elif typ in ("time", "time_window", "xgboost"):
            from backend.ml.time_predictor import get_time_predictor
            return get_time_predictor()
        else:
            raise ValueError(f"Unknown predictor type: {model_type!r}. Supported: 'risk', 'amount', 'time'.")
