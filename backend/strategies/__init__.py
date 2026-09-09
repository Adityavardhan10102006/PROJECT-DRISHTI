"""
backend/strategies — Project DRISHTI Strategy Layer
====================================================
Exposes polymorphic scoring and prediction strategies.
"""

from backend.strategies.prediction_strategy import (
    PredictionStrategy,
    MLPredictionStrategy,
    HeuristicPredictionStrategy,
)
from backend.strategies.atm_scoring_strategy import (
    ATMScoringStrategy,
    DistanceScoringStrategy,
    RiskScoringStrategy,
    CompositeATMScoringStrategy,
)

__all__ = [
    "PredictionStrategy",
    "MLPredictionStrategy",
    "HeuristicPredictionStrategy",
    "ATMScoringStrategy",
    "DistanceScoringStrategy",
    "RiskScoringStrategy",
    "CompositeATMScoringStrategy",
]
