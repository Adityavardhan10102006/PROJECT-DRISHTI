"""
models.py — Project DRISHTI
============================
Pydantic data models (schemas) used across the API.

Day 1: Basic request/response shapes.
Day 2+: Extended with NLP extraction fields, DBSCAN cluster output,
        XGBoost prediction payload, and NetworkX mule graph results.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class FraudType(str, Enum):
    upi_fraud = "upi_fraud"
    kyc_fraud = "kyc_fraud"
    phishing  = "phishing"


# ─────────────────────────────────────────────
# INCOMING COMPLAINT (POST /predict request)
# ─────────────────────────────────────────────

class ComplaintIn(BaseModel):
    """
    Raw complaint submitted by a police officer or intake system.
    All fields except complaint_text are optional — the NLP parser
    (Day 2) will attempt to extract missing fields from free text.
    """
    complaint_id:   Optional[str]       = Field(None,  description="System-assigned or officer-entered ID")
    complaint_text: str                  = Field(...,   description="Free-text complaint in Hindi/English/Hinglish")
    timestamp:      Optional[datetime]  = Field(None,  description="Time of incident (defaults to now if absent)")
    victim_lat:     Optional[float]     = Field(None,  description="Victim's approximate latitude")
    victim_lon:     Optional[float]     = Field(None,  description="Victim's approximate longitude")
    fraud_type:     Optional[FraudType] = Field(None,  description="Type of cyber fraud (auto-detected if absent)")
    amount:         Optional[float]     = Field(None,  description="Fraudulent amount in INR")
    transaction_id: Optional[str]       = Field(None,  description="UPI / bank reference number")
    bank_account:   Optional[str]       = Field(None,  description="Suspect's bank account number")
    ifsc_code:      Optional[str]       = Field(None,  description="IFSC of suspect's bank branch")

    class Config:
        json_schema_extra = {
            "example": {
                "complaint_text": "Mujhe UPI pe ek request aayi ₹15,000 ki — PIN daala aur paise chale gaye.",
                "victim_lat": 19.076,
                "victim_lon": 72.877,
                "fraud_type": "upi_fraud",
                "amount": 15000
            }
        }


# ─────────────────────────────────────────────
# HOTSPOT COORDINATE
# ─────────────────────────────────────────────

class HotspotLocation(BaseModel):
    """
    A predicted cash-withdrawal hotspot.
    Produced by DBSCAN clustering of nearby ATMs (Day 2).
    """
    lat:          float = Field(..., description="Cluster centroid latitude")
    lon:          float = Field(..., description="Cluster centroid longitude")
    radius_km:    float = Field(..., description="Estimated search radius in km")
    atm_count:    int   = Field(..., description="Number of ATMs/branches in this cluster")
    confidence:   float = Field(..., description="Model confidence score 0–1")
    cluster_id:   int   = Field(..., description="DBSCAN cluster label")


# ─────────────────────────────────────────────
# TIME-WINDOW PREDICTION
# ─────────────────────────────────────────────

class TimeWindow(BaseModel):
    """
    Predicted time window for cash withdrawal.
    Produced by XGBoost regressor (Day 3).
    """
    earliest_minutes: int   = Field(..., description="Earliest expected withdrawal (minutes after complaint)")
    latest_minutes:   int   = Field(..., description="Latest expected withdrawal (minutes after complaint)")
    peak_minutes:     int   = Field(..., description="Most likely withdrawal time (minutes after complaint)")
    confidence:       float = Field(..., description="Prediction confidence 0–1")
    model_source:     Optional[str] = Field("xgboost", description="Model source: xgboost or rule_based_fallback")


# ─────────────────────────────────────────────
# MULE ACCOUNT
# ─────────────────────────────────────────────

class MuleAccount(BaseModel):
    """
    A flagged mule account from the transaction graph.
    Produced by NetworkX community detection & centrality analysis.
    """
    account_number:   str         = Field(..., description="Bank account number")
    ifsc_code:        str         = Field(..., description="IFSC code")
    bank_name:        Optional[str] = Field(None, description="Bank name")
    risk_score:       float       = Field(..., description="Risk score 0–1 (1 = definite mule)")
    linked_accounts:  List[str]   = Field(default_factory=list, description="Connected accounts in the network")
    transaction_count: int        = Field(..., description="Number of pass-through transactions")
    centrality:       Optional[float] = Field(None, description="Betweenness centrality score")
    flag_reason:      str         = Field(..., description="Human-readable reason for flagging")
    is_historical_mule: bool      = Field(False, description="Whether account has historically high betweenness centrality")


# ─────────────────────────────────────────────
# MULTI-HOP MONEY TRAIL
# ─────────────────────────────────────────────

class MoneyTrailHop(BaseModel):
    hop_index:          int
    from_account:       str
    to_account:         str
    to_bank:            Optional[str] = None
    to_ifsc:            Optional[str] = None
    amount:             float
    commission_retained: float = 0.0
    timestamp:          str
    minutes_from_start: int
    txn_type:           str = "IMPS"
    txn_ref:            Optional[str] = None
    is_terminal_cashout: bool = False


class MoneyTrail(BaseModel):
    starting_account:       str
    hop_count:              int
    initial_amount:         float
    final_cashout_amount:   float
    trail_duration_minutes: int
    hops:                   List[MoneyTrailHop] = Field(default_factory=list)
    mule_accounts:          List[MuleAccount] = Field(default_factory=list)
    graph_metrics:          Dict[str, Any] = Field(default_factory=dict)
    data_source:            Optional[str] = Field("transaction_dataset", description="Provenance of money trail: transaction_dataset or synthetic_fallback")


# ─────────────────────────────────────────────
# TOP-K LOCATIONS & FEASIBILITY
# ─────────────────────────────────────────────

class PoliceFeasibility(BaseModel):
    nearest_unit_id:         str
    unit_name:               str
    unit_vehicle:            str
    unit_lat:                float
    unit_lon:                float
    distance_km:             float
    eta_minutes:             float
    peak_withdrawal_minutes: int
    time_margin_minutes:     float
    feasibility_score:       float
    feasibility_status:      str
    feasibility_desc:        str
    composite_priority:      float
    estimated_distance:      Optional[float] = None
    estimated_response_time: Optional[float] = None
    priority:                Optional[float] = None
    data_mode:               Optional[str] = "curated_static_demo"


class TopKLocation(BaseModel):
    rank:                 int
    location_name:        str
    lat:                  float
    lon:                  float
    radius_km:            float
    atm_count:            int
    probability:          float
    confidence:           float
    distance_km:          Optional[float] = None
    priority_rank:        Optional[int] = None
    interception_priority: Optional[float] = None
    feasibility:          Optional[PoliceFeasibility] = None
    # Enhanced ATM Candidate Specifications
    atm_id:               Optional[str] = None
    bank:                 Optional[str] = None
    area:                 Optional[str] = None
    risk_score:           Optional[float] = None
    predicted_time_window: Optional[str] = None
    predicted_amount:     Optional[float] = None
    reason:               Optional[str] = None
    is_24x7:              Optional[bool] = None


# ─────────────────────────────────────────────
# 5D INTELLIGENCE OUTPUT
# ─────────────────────────────────────────────

class FiveDIntelligence(BaseModel):
    where:  Dict[str, Any] = Field(..., description="WHERE: Primary cash-out coordinates, radius, top candidates")
    when:   Dict[str, Any] = Field(..., description="WHEN: Predicted time window, countdown, urgency status")
    amount: Dict[str, Any] = Field(..., description="AMOUNT: Reported amount, trail volume, estimated cash-out")
    why:    Dict[str, Any] = Field(..., description="WHY: Explainable AI plain-English rationale and risk signals")
    action: Dict[str, Any] = Field(..., description="ACTION: Concrete law enforcement SOP and dispatch priority")


# ─────────────────────────────────────────────
# PREDICTION RESPONSE (POST /predict response)
# ─────────────────────────────────────────────

class PredictionOut(BaseModel):
    """
    Full prediction result returned to the dashboard/police officer.
    Backward-compatible with Day 1-3 dashboard while exposing rich 5D intelligence.
    """
    alert_id:            Optional[int]          = Field(None, description="Unique SQLite database Alert record ID")
    complaint_id:        str                    = Field(...,  description="Echo of the incoming complaint ID")
    fraud_type:          FraudType              = Field(...,  description="Detected or confirmed fraud type")
    amount:              Optional[float]        = Field(None, description="Fraud amount (extracted or provided)")
    extraction_confidence: Optional[float]      = Field(None, description="NLP key entity extraction confidence score (0.0–1.0)")
    is_historical_mule:  Optional[bool]         = Field(None, description="Flagged if any account in the prediction has historically high betweenness centrality")
    hotspot:             Optional[HotspotLocation] = Field(None, description="DBSCAN predicted withdrawal cluster")
    time_window:         Optional[TimeWindow]      = Field(None, description="XGBoost predicted withdrawal window")
    mule_accounts:       List[MuleAccount]         = Field(default_factory=list, description="NetworkX flagged accounts")
    nlp_entities:        Dict[str, Any]            = Field(default_factory=dict, description="Entities extracted by NLP model")
    alert_level:         str                       = Field("LOW", description="Urgency: LOW | MEDIUM | HIGH | CRITICAL")
    processed_at:        datetime                  = Field(default_factory=datetime.utcnow)
    model_versions:      Dict[str, str]            = Field(default_factory=dict, description="Versions of each sub-model used")

    # Day 4+ Upgraded Intelligence Attributes
    five_d:              Optional[FiveDIntelligence] = Field(None, description="5D Cybercrime Intelligence dimensions")
    top_k_locations:     List[TopKLocation]         = Field(default_factory=list, description="Top-K ranked withdrawal locations")
    money_trail:         Optional[MoneyTrail]       = Field(None, description="Full multi-hop money flow laundering chain")
    feasibility:         Optional[PoliceFeasibility] = Field(None, description="Primary interception feasibility and unit ETA")
    geojson_risk_layer:  Optional[Dict[str, Any]]   = Field(None, description="GeoJSON FeatureCollection for heatmap rendering")
    risk_score:          Optional[float]            = Field(None, description="AI/ML risk score 0–100")
    risk_tier:           Optional[str]              = Field(None, description="AI/ML risk tier: LOW | MEDIUM | HIGH | CRITICAL")
    data_sources:        Optional[Dict[str, str]]   = Field(default_factory=dict, description="Provenance metadata for datasets used in prediction")


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:    str = "ok"
    version:   str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, str] = Field(
        default_factory=lambda: {
            "database":  "not_connected",   # Day 1 stub
            "nlp_model": "not_loaded",      # Day 2
            "ml_model":  "not_loaded",      # Day 3
            "graph_engine": "not_loaded",   # Day 3
        }
    )
