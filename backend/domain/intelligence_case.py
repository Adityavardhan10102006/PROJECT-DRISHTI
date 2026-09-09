"""
backend/domain/intelligence_case.py — Project DRISHTI
======================================================
Central domain object representing a complete cybercrime case investigation.
Exemplifies OOP Composition by combining Complaint, MoneyTrail,
Predictions, ATM candidates, Police Feasibility, and FiveDIntelligence.
"""

from typing import Dict, Any, List, Optional
from backend.domain.complaint import Complaint
from backend.domain.money_trail import MoneyTrail
from backend.domain.prediction import RiskPrediction, AmountPrediction, TimePrediction


class FiveDIntelligence:
    """
    Domain object encapsulating the 5 Dimensions of Actionable Intelligence:
      - WHERE:  Target ATM / Geo-hotspot
      - WHEN:   Withdrawal Time-Window & Urgency
      - AMOUNT: Expected Cash-out / Loss range
      - WHY:    Explainable AI Risk Factors & Typology
      - ACTION: Immediate Police Protocol & Dispatch Directive
    """

    def __init__(
        self,
        where: Dict[str, Any],
        when: Dict[str, Any],
        amount: Dict[str, Any],
        why: Dict[str, Any],
        action: Dict[str, Any],
        confidence_summary: Optional[Dict[str, Any]] = None,
    ):
        self.where = where
        self.when = when
        self.amount = amount
        self.why = why
        self.action = action
        self.confidence_summary = confidence_summary or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes 5D Intelligence object to dictionary."""
        return {
            "where": self.where,
            "when": self.when,
            "amount": self.amount,
            "why": self.why,
            "action": self.action,
            "confidence_summary": self.confidence_summary,
        }

    def __repr__(self) -> str:
        return f"<FiveDIntelligence where={self.where.get('primary_location', 'N/A')!r}>"


class IntelligenceCase:
    """
    Central composite entity aggregating all facets of a DRISHTI cybercrime investigation.

    Composition:
      - complaint: Complaint
      - money_trail: MoneyTrail
      - risk_prediction: RiskPrediction
      - amount_prediction: AmountPrediction
      - time_prediction: TimePrediction
      - top_k_atms: List[Dict[str, Any]]
      - police_feasibility: Optional[Dict[str, Any]]
      - five_d: FiveDIntelligence
    """

    def __init__(
        self,
        complaint: Complaint,
        money_trail: MoneyTrail,
        risk_prediction: RiskPrediction,
        amount_prediction: AmountPrediction,
        time_prediction: TimePrediction,
        top_k_atms: List[Dict[str, Any]],
        five_d: FiveDIntelligence,
        police_feasibility: Optional[Dict[str, Any]] = None,
        geojson_layer: Optional[Dict[str, Any]] = None,
        hotspot: Optional[Dict[str, Any]] = None,
        nlp_entities: Optional[Dict[str, Any]] = None,
        extraction_confidence: float = 1.0,
    ):
        self.complaint = complaint
        self.money_trail = money_trail
        self.risk_prediction = risk_prediction
        self.amount_prediction = amount_prediction
        self.time_prediction = time_prediction
        self.top_k_atms = top_k_atms
        self.five_d = five_d
        self.police_feasibility = police_feasibility
        self.geojson_layer = geojson_layer or {}
        self.hotspot = hotspot
        self.nlp_entities = nlp_entities or {}
        self.extraction_confidence = float(extraction_confidence)

    @property
    def case_id(self) -> str:
        return self.complaint.case_id

    @property
    def risk_score(self) -> float:
        return self.risk_prediction.risk_score

    @property
    def risk_level(self) -> str:
        return self.risk_prediction.risk_level

    @property
    def is_actionable(self) -> bool:
        """Determines if the case has actionable ATM candidates and sufficient feasibility margin."""
        if not self.top_k_atms:
            return False
        if self.police_feasibility and self.police_feasibility.get("feasibility_status") == "WINDOW_EXPIRED":
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes full IntelligenceCase into a dictionary representation."""
        return {
            "complaint": self.complaint.to_dict(),
            "money_trail": self.money_trail.to_dict(),
            "risk_prediction": self.risk_prediction.to_dict(),
            "amount_prediction": self.amount_prediction.to_dict(),
            "time_prediction": self.time_prediction.to_dict(),
            "top_k_locations": self.top_k_atms,
            "police_feasibility": self.police_feasibility,
            "five_d": self.five_d.to_dict(),
            "geojson_layer": self.geojson_layer,
            "hotspot": self.hotspot,
            "nlp_entities": self.nlp_entities,
            "extraction_confidence": self.extraction_confidence,
            "is_actionable": self.is_actionable,
        }

    def __repr__(self) -> str:
        return (
            f"<IntelligenceCase id={self.case_id!r} "
            f"risk={self.risk_prediction.risk_score} "
            f"hops={self.money_trail.hop_count()}>"
        )
