"""
backend/services/feasibility_service.py — Project DRISHTI
==========================================================
Service encapsulating police response calculations and dispatch prioritisation.
Separates PoliceUnit domain entities from calculation and ranking algorithms.
"""

from typing import List, Dict, Any, Optional, Tuple
from backend.domain.police_unit import PoliceUnit
from backend.ml.feasibility import get_feasibility_engine, FeasibilityEngine


class FeasibilityCalculator:
    """
    Service responsible for geospatial dispatch feasibility calculations.

    Encapsulation:
      - Interacts with PoliceUnit domain entities.
      - Computes distance, transit ETA, interception margin, and composite action priority.
    """

    def __init__(self, engine: Optional[FeasibilityEngine] = None):
        self._engine = engine or get_feasibility_engine()

    def get_police_units(self) -> List[PoliceUnit]:
        """Returns registered police units as PoliceUnit domain entities."""
        units = []
        for u in self._engine.registry:
            units.append(
                PoliceUnit(
                    unit_id=u.get("unit_id", "UNIT-01"),
                    unit_name=u.get("name", "Patrol Unit"),
                    station_name=u.get("name", "Police Station"),
                    latitude=float(u.get("lat", u.get("latitude", 0.0))),
                    longitude=float(u.get("lon", u.get("longitude", 0.0))),
                    speed_kmh=float(u.get("speed_kmh", 35.0)),
                    is_available=True,
                )
            )
        return units

    def find_nearest_unit(self, target_lat: float, target_lon: float) -> Tuple[Optional[PoliceUnit], float]:
        """Finds closest police unit and returns (unit, distance_km)."""
        units = self.get_police_units()
        if not units:
            return None, 999.0
        nearest = min(units, key=lambda u: u.distance_to(target_lat, target_lon))
        dist = nearest.distance_to(target_lat, target_lon)
        return nearest, dist

    def calculate(
        self,
        target_lat: float,
        target_lon: float,
        peak_withdrawal_minutes: int,
        case_risk_score: float,
    ) -> Dict[str, Any]:
        """Calculates feasibility metrics for a target location."""
        return self._engine.calculate_feasibility(
            target_lat=target_lat,
            target_lon=target_lon,
            peak_withdrawal_minutes=peak_withdrawal_minutes,
            case_risk_score=case_risk_score,
        )

    def rank_top_k_candidates(
        self,
        top_k_locations: List[Dict[str, Any]],
        peak_withdrawal_minutes: int,
        case_risk_score: float,
    ) -> List[Dict[str, Any]]:
        """Ranks candidate ATM locations by interception feasibility and margin."""
        return self._engine.rank_top_k_candidates(
            top_k_locations=top_k_locations,
            peak_withdrawal_minutes=peak_withdrawal_minutes,
            case_risk_score=case_risk_score,
        )


_feasibility_calculator_instance: Optional[FeasibilityCalculator] = None

def get_feasibility_calculator() -> FeasibilityCalculator:
    global _feasibility_calculator_instance
    if _feasibility_calculator_instance is None:
        _feasibility_calculator_instance = FeasibilityCalculator()
    return _feasibility_calculator_instance
