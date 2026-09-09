"""
backend/services/atm_service.py — Project DRISHTI
==================================================
ATM Prediction Service encapsulating ATM catalog management,
candidate geospatial filtering, and scoring strategies.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import pandas as pd

from backend.domain.atm import ATM
from backend.strategies.atm_scoring_strategy import (
    ATMScoringStrategy,
    CompositeATMScoringStrategy,
)
from backend.ml.location_predictor import get_location_predictor, LocationPredictor

DEFAULT_ATMS_CSV = "data/hyderabad_atms.csv"


class ATMPredictor:
    """
    Service responsible for ATM candidate retrieval, scoring, and ranking.

    Architecture:
      - Interacts with ATM domain entities.
      - Uses polymorphic ATMScoringStrategy for heuristic/distance scoring.
      - Integrates with trained calibrated ML LocationPredictor for primary scoring.
    """

    def __init__(
        self,
        catalog_path: str = DEFAULT_ATMS_CSV,
        scoring_strategy: Optional[ATMScoringStrategy] = None,
        location_engine: Optional[LocationPredictor] = None,
    ):
        self.catalog_path = catalog_path
        self.scoring_strategy = scoring_strategy or CompositeATMScoringStrategy()
        self._location_engine = location_engine or get_location_predictor()
        self._atms: List[ATM] = []
        self._load_atm_catalog()

    def _load_atm_catalog(self) -> None:
        """Loads ATM records from CSV into ATM domain entities."""
        try:
            df = pd.read_csv(self.catalog_path, encoding="utf-8")
            atms = []
            for _, row in df.iterrows():
                atms.append(
                    ATM(
                        atm_id=str(row.get("atm_id", f"ATM-{len(atms)+1}")),
                        bank=str(row.get("bank", "Bank")),
                        latitude=float(row.get("latitude", 0.0)),
                        longitude=float(row.get("longitude", 0.0)),
                        area=row.get("area"),
                        locality=row.get("locality"),
                        city=str(row.get("city", "Hyderabad")),
                        pincode=str(row.get("pincode", "")) if pd.notna(row.get("pincode")) else None,
                        is_24x7=bool(row.get("is_24x7", True)),
                        accessibility=str(row.get("accessibility", "HIGH")),
                        historical_mule_hits=int(row.get("historical_mule_hits", 0) or 0),
                    )
                )
            self._atms = atms
        except Exception as exc:
            print(f"[DRISHTI-ATM] Warning: could not load ATM catalog ({exc})")
            self._atms = []

    def get_all_atms(self) -> List[ATM]:
        """Returns all loaded ATM domain objects."""
        return list(self._atms)

    def filter_candidates(
        self,
        victim_lat: float,
        victim_lon: float,
        max_distance_km: float = 15.0,
    ) -> List[ATM]:
        """Filters ATMs within max_distance_km radius."""
        candidates = []
        for atm in self._atms:
            dist = atm.distance_to(victim_lat, victim_lon)
            if dist <= max_distance_km:
                candidates.append(atm)
        return candidates

    def score_candidates(
        self,
        candidates: List[ATM],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Scores candidate ATMs using the configured scoring strategy."""
        results = []
        for atm in candidates:
            score = self.scoring_strategy.score(atm, context)
            results.append({
                "atm": atm,
                "score": score,
                "distance_km": atm.distance_to(context.get("victim_lat", 0.0), context.get("victim_lon", 0.0)),
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def predict_top_k(
        self,
        victim_lat: Optional[float],
        victim_lon: Optional[float],
        amount: float,
        fraud_type: str = "upi_fraud",
        complaint_dt: Optional[datetime] = None,
        city: Optional[str] = None,
        k: int = 3,
        graph_metrics: Optional[Dict[str, Any]] = None,
        demo_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes primary ML candidate prediction, delegating to the trained
        calibrated LocationPredictor engine.
        """
        return self._location_engine.predict_top_k(
            victim_lat=victim_lat,
            victim_lon=victim_lon,
            amount=amount,
            fraud_type=fraud_type,
            complaint_dt=complaint_dt,
            city=city,
            k=k,
            graph_metrics=graph_metrics,
            demo_mode=demo_mode,
        )


_atm_predictor_instance: Optional[ATMPredictor] = None

def get_atm_predictor() -> ATMPredictor:
    global _atm_predictor_instance
    if _atm_predictor_instance is None:
        _atm_predictor_instance = ATMPredictor()
    return _atm_predictor_instance
