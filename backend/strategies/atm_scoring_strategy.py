"""
backend/strategies/atm_scoring_strategy.py — Project DRISHTI
=============================================================
Polymorphic strategy pattern for ATM candidate terminal evaluation and ranking.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.domain.atm import ATM


class ATMScoringStrategy(ABC):
    """
    Abstract Strategy for evaluating and scoring candidate ATM terminals.
    """

    @abstractmethod
    def score(self, atm: ATM, context: Dict[str, Any]) -> float:
        """Computes a normalized affinity score [0.0, 1.0] for the ATM."""
        pass


class DistanceScoringStrategy(ATMScoringStrategy):
    """
    Evaluates ATM proximity based on exponential spatial decay from victim/incident coordinates.
    """

    def __init__(self, decay_km: float = 3.0, max_distance_km: Optional[float] = None):
        self.decay_km = decay_km
        self.max_distance_km = max_distance_km

    def score(self, atm: ATM, context: Dict[str, Any]) -> float:
        vic_lat = context.get("victim_lat")
        vic_lon = context.get("victim_lon")
        if vic_lat is None or vic_lon is None:
            return 0.5

        dist_km = atm.distance_to(vic_lat, vic_lon)
        if self.max_distance_km and dist_km > self.max_distance_km:
            return 0.0
        # Exponential spatial decay
        import math
        return float(round(math.exp(-dist_km / self.decay_km), 4))


class RiskScoringStrategy(ATMScoringStrategy):
    """
    Evaluates ATM based on historical mule activity and 24x7 operational vulnerability.
    """

    def score(self, atm: ATM, context: Dict[str, Any]) -> float:
        if "case_risk_score" in context:
            return float(round(context["case_risk_score"] / 100.0, 4))

        base_score = 0.4
        if atm.is_24x7:
            base_score += 0.2
        if atm.historical_mule_hits > 0:
            base_score += min(0.4, atm.historical_mule_hits * 0.1)
        return min(1.0, base_score)


class CompositeATMScoringStrategy(ATMScoringStrategy):
    """
    Combines spatial proximity, historical syndication risk, and accessibility using weighted composition.
    """

    def __init__(
        self,
        distance_strategy: Optional[ATMScoringStrategy] = None,
        risk_strategy: Optional[ATMScoringStrategy] = None,
        dist_weight: float = 0.65,
        risk_weight: float = 0.35,
        strategies: Optional[List[Any]] = None,
    ):
        if strategies is not None:
            self.strategies = strategies
        else:
            self.strategies = [
                (distance_strategy or DistanceScoringStrategy(), dist_weight),
                (risk_strategy or RiskScoringStrategy(), risk_weight),
            ]
        self.distance_strategy = distance_strategy or DistanceScoringStrategy()
        self.risk_strategy = risk_strategy or RiskScoringStrategy()
        self.dist_weight = dist_weight
        self.risk_weight = risk_weight

    def score(self, atm: ATM, context: Dict[str, Any]) -> float:
        total_score = 0.0
        total_weight = 0.0
        for item in self.strategies:
            if isinstance(item, (list, tuple)):
                strat, weight = item[0], item[1]
            else:
                strat, weight = item, 1.0
            total_score += strat.score(atm, context) * weight
            total_weight += weight
        return float(round(total_score / total_weight, 4)) if total_weight > 0 else 0.0
