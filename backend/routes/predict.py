"""
routes/predict.py — Project DRISHTI (Day 3 — XGBoost wired)
=============================================================
POST /predict endpoint.

Day 1: Stub — hard-coded demo values.
Day 2: Real NLP extraction (regex+keywords) + DBSCAN hotspot clustering.
Day 3: XGBoost time predictor wired. Mule graph stub (Day 4).
Day 4: NetworkX mule graph + WebSocket push to React dashboard.
"""

import uuid
import json
import random as _rnd
from datetime import datetime
from fastapi import APIRouter, status
from typing import Optional

from backend.models import (
    ComplaintIn,
    PredictionOut,
    FraudType,
    HotspotLocation,
    TimeWindow,
    MuleAccount,
    MoneyTrail,
    MoneyTrailHop,
    TopKLocation,
    PoliceFeasibility,
    FiveDIntelligence,
)
from backend.nlp.extractor          import ComplaintExtractor
from backend.clustering.hotspot     import HotspotPredictor
from backend.ml.mule_graph          import get_mule_graph
from backend.ml.risk_predictor      import get_risk_predictor
from backend.ml.feasibility         import get_feasibility_engine
from backend.clustering.geo_risk    import get_geo_risk_engine
from backend.ml.explainability      import get_5d_engine

router = APIRouter(prefix="/predict", tags=["Prediction"])

# ─────────────────────────────────────────────
# MODULE-LEVEL SINGLETONS
# ─────────────────────────────────────────────
_extractor  = ComplaintExtractor()
_hotspot    = HotspotPredictor(eps_km=0.5, min_samples=2)
_time_model = None   # populated by _get_time_model() on first call


def _get_time_model():
    """
    Lazy-load the XGBoost predictor so the server still starts even if the
    model file hasn't been trained yet (returns None → falls back to rules).
    """
    global _time_model
    if _time_model is not None:
        return _time_model
    try:
        from backend.ml.time_predictor import TimeWindowPredictor
        _time_model = TimeWindowPredictor()
    except FileNotFoundError as e:
        print(f"[DRISHTI] XGBoost model not found ({e}). "
              f"Using rule-based fallback. Train with: python -m backend.ml.train_xgboost")
        _time_model = None
    except Exception as e:
        print(f"[DRISHTI] XGBoost load error: {e}. Using rule-based fallback.")
        _time_model = None
    return _time_model


# ─────────────────────────────────────────────
# HELPER: Rule-based time window fallback
# Used when XGBoost model file is absent.
# ─────────────────────────────────────────────
_RULE_WINDOWS = {
    "upi_fraud": (20, 60, 35),   # (earliest, latest, peak)
    "kyc_fraud": (10, 50, 25),
    "phishing":  (35, 90, 55),
}

def _rule_based_window(fraud_type: str) -> TimeWindow:
    earliest, latest, peak = _RULE_WINDOWS.get(fraud_type, (20, 80, 40))
    return TimeWindow(
        earliest_minutes=earliest,
        latest_minutes=latest,
        peak_minutes=peak,
        confidence=0.50,
    )


# ─────────────────────────────────────────────
# HELPER: Alert level
# ─────────────────────────────────────────────
def compute_alert_level(amount: float, fraud_type: str, peak_minutes: int = 40) -> str:
    """
    Urgency = f(amount, time remaining).
    High amount + short withdrawal window = CRITICAL.
    """
    if amount >= 100000 or (amount >= 50000 and peak_minutes <= 30):
        return "CRITICAL"
    elif amount >= 25000:
        return "HIGH"
    elif amount >= 5000:
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────
# POST /predict
# ─────────────────────────────────────────────
@router.post(
    "/",
    response_model=PredictionOut,
    status_code=status.HTTP_200_OK,
    summary="Submit a cybercrime complaint for hotspot + time-window prediction",
    description=(
        "Returns:\n"
        "- **hotspot**: DBSCAN-predicted ATM cluster (lat/lon/radius)\n"
        "- **time_window**: XGBoost-predicted minutes-to-withdrawal window\n"
        "- **mule_accounts**: NetworkX flagged accounts (Day 4)\n\n"
        "Day 3: XGBoost time predictor live."
    ),
)
async def predict(complaint: ComplaintIn) -> PredictionOut:
    """
    Day 3 pipeline:
      1. NLP extraction from complaint_text
      2. Merge NLP + explicit fields
      3. DBSCAN hotspot around victim lat/lon
      4. XGBoost withdrawal time prediction
      5. Mule detection stub (Day 4)
    """

    # ── 1. Complaint ID ───────────────────────────────────────────
    cid = complaint.complaint_id or f"DRISHTI-{uuid.uuid4().hex[:8].upper()}"

    # ── 2. NLP extraction ─────────────────────────────────────────
    nlp = _extractor.extract(complaint.complaint_text)

    # ── 3. Merge fields (explicit > NLP > default) ────────────────
    fraud_type_str = (
        complaint.fraud_type.value
        if complaint.fraud_type
        else nlp.fraud_type or "upi_fraud"
    )
    fraud_type = FraudType(fraud_type_str)

    amount   = complaint.amount or nlp.amount or 0.0
    txn_id   = complaint.transaction_id or nlp.transaction_id
    account  = complaint.bank_account   or nlp.bank_account
    ifsc     = complaint.ifsc_code      or nlp.ifsc_code

    # Resolve complaint timestamp for feature engineering
    complaint_dt = complaint.timestamp or datetime.utcnow()

    # City — not in ComplaintIn, so infer from lat/lon bucket if possible.
    # Simplified for Day 3; Day 4: reverse-geocode against PostGIS city polygons.
    city = _infer_city(complaint.victim_lat, complaint.victim_lon)

    # ── 4. DBSCAN Top-K Hotspots ──────────────────────────────────
    hotspot_out = None
    top_k_locations_out: list[TopKLocation] = []
    top_k_raw: list[dict] = []

    if complaint.victim_lat and complaint.victim_lon:
        vic_lat, vic_lon = complaint.victim_lat, complaint.victim_lon

        # Deterministic synthetic ATM grid (seeded per location, 8-10 points for rich clustering)
        _rnd.seed(int(abs(vic_lat * 1000 + vic_lon * 1000)))
        synthetic_atms = [
            {
                "lat": round(vic_lat + _rnd.uniform(-0.015, 0.015), 6),
                "lon": round(vic_lon + _rnd.uniform(-0.015, 0.015), 6),
                "type": _rnd.choice(["ATM", "branch", "micro_ATM", "CSP"]),
                "bank": _rnd.choice(["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank"])
            }
            for _ in range(8)
        ]
        
        # Legacy single hotspot
        result = _hotspot.predict_single(synthetic_atms, vic_lat, vic_lon)
        if result:
            hotspot_out = HotspotLocation(
                lat=result.lat,
                lon=result.lon,
                radius_km=result.radius_km,
                atm_count=result.atm_count,
                confidence=result.confidence,
                cluster_id=result.cluster_id,
            )

        # Top-K candidate cash-out locations
        top_k_raw = _hotspot.predict_top_k(synthetic_atms, vic_lat, vic_lon, k=3)

    # ── 5. XGBoost time prediction ────────────────────────────────
    model = _get_time_model()
    if model:
        tw = model.predict(
            fraud_type=fraud_type_str,
            amount=amount,
            complaint_dt=complaint_dt,
            city=city,
        )
        time_window_out = TimeWindow(
            earliest_minutes=tw.earliest_minutes,
            latest_minutes=tw.latest_minutes,
            peak_minutes=tw.peak_minutes,
            confidence=tw.confidence,
        )
        xgb_version = "xgboost-v2.0-trained"
    else:
        time_window_out = _rule_based_window(fraud_type_str)
        xgb_version = "rule-based-fallback"

    # ── 6. Multi-Hop Money-Trail Analysis (NetworkX) ──────────────
    mule_engine = get_mule_graph()
    trail_data = mule_engine.trace_trail(
        starting_account=account,
        initial_amount=amount,
        incident_time=complaint_dt,
        max_hops=4,
    )

    money_trail_hops = [
        MoneyTrailHop(**h) for h in trail_data.get("hops", [])
    ]
    mule_accounts_list = [
        MuleAccount(**m) for m in trail_data.get("mule_accounts", [])
    ]

    money_trail_out = MoneyTrail(
        starting_account=trail_data["starting_account"],
        hop_count=trail_data["hop_count"],
        initial_amount=trail_data["initial_amount"],
        final_cashout_amount=trail_data["final_cashout_amount"],
        trail_duration_minutes=trail_data["trail_duration_minutes"],
        hops=money_trail_hops,
        mule_accounts=mule_accounts_list,
        graph_metrics=trail_data.get("graph_metrics", {}),
    )

    # ── 7. AI/ML Case Risk Prediction ─────────────────────────────
    risk_engine = get_risk_predictor()
    max_centrality = trail_data.get("graph_metrics", {}).get("max_betweenness", 0.05)
    risk_res = risk_engine.predict(
        fraud_type=fraud_type_str,
        amount=amount,
        hop_count=trail_data["hop_count"],
        centrality=max_centrality,
        complaint_dt=complaint_dt,
        est_withdrawal_mins=time_window_out.peak_minutes,
    )
    risk_score = risk_res["risk_score"]
    risk_tier = risk_res["risk_level"]

    # ── 8. Feasibility & Response Prioritisation ──────────────────
    feas_engine = get_feasibility_engine()
    top_k_ranked = feas_engine.rank_top_k_candidates(
        top_k_locations=top_k_raw,
        peak_withdrawal_minutes=time_window_out.peak_minutes,
        case_risk_score=risk_score,
    )

    top_k_locations_out = [
        TopKLocation(
            rank=loc["rank"],
            location_name=loc["location_name"],
            lat=loc["lat"],
            lon=loc["lon"],
            radius_km=loc["radius_km"],
            atm_count=loc["atm_count"],
            probability=loc["probability"],
            confidence=loc["confidence"],
            distance_km=loc.get("distance_km"),
            priority_rank=loc.get("priority_rank"),
            interception_priority=loc.get("interception_priority"),
            feasibility=PoliceFeasibility(**loc["feasibility"]) if loc.get("feasibility") else None,
        )
        for loc in top_k_ranked
    ]

    primary_feasibility_out = (
        PoliceFeasibility(**top_k_ranked[0]["feasibility"])
        if (top_k_ranked and top_k_ranked[0].get("feasibility"))
        else None
    )

    # ── 9. Geospatial Risk Heatmap Layer (GeoJSON) ────────────────
    geo_risk_engine = get_geo_risk_engine()
    geojson_layer = geo_risk_engine.generate_risk_geojson(
        victim_lat=complaint.victim_lat,
        victim_lon=complaint.victim_lon,
        top_k_locations=top_k_ranked,
        police_unit=top_k_ranked[0]["feasibility"] if top_k_ranked else None,
        case_risk_score=risk_score,
    )

    # ── 10. "5D Intelligence" Synthesis & Explainability ──────────
    five_d_engine = get_5d_engine()
    five_d_payload = five_d_engine.build_5d_intelligence(
        complaint_id=cid,
        fraud_type=fraud_type_str,
        amount=amount,
        hotspot=hotspot_out.model_dump() if hotspot_out else None,
        top_k_locations=top_k_ranked,
        time_window=time_window_out.model_dump() if time_window_out else None,
        money_trail=trail_data,
        risk_result=risk_res,
        feasibility=top_k_ranked[0]["feasibility"] if top_k_ranked else None,
        city=city,
    )
    five_d_out = FiveDIntelligence(**five_d_payload)

    # ── 11. Legacy alert level (for backward compatibility) ────────
    legacy_alert_level = compute_alert_level(
        amount, fraud_type_str, time_window_out.peak_minutes
    )

    # ── 12. NLP entities dict ─────────────────────────────────────
    nlp_entities = {
        "nlp_fraud_type":       nlp.fraud_type,
        "nlp_fraud_confidence": nlp.fraud_type_confidence,
        "nlp_amount":           nlp.amount,
        "nlp_upi_id":           nlp.upi_id,
        "nlp_transaction_id":   nlp.transaction_id,
        "nlp_bank_account":     nlp.bank_account,
        "nlp_ifsc":             nlp.ifsc_code,
        "nlp_phone":            nlp.phone_number,
        "used_fraud_type":      fraud_type_str,
        "used_amount":          amount,
        "used_txn_id":          txn_id,
        "inferred_city":        city,
        "extraction_method":    nlp.extraction_method,
    }

    return PredictionOut(
        complaint_id=cid,
        fraud_type=fraud_type,
        amount=amount,
        hotspot=hotspot_out,
        time_window=time_window_out,
        mule_accounts=mule_accounts_list,
        nlp_entities=nlp_entities,
        alert_level=legacy_alert_level,
        processed_at=datetime.utcnow(),
        model_versions={
            "nlp":      "regex-keywords-v0.2",
            "dbscan":   "sklearn-v1.5-eps0.5km-topk",
            "xgboost":  xgb_version,
            "networkx": "multihop-graph-v1.0",
            "risk_ai":  risk_res.get("model_version", "gbc-v1.0"),
        },
        five_d=five_d_out,
        top_k_locations=top_k_locations_out,
        money_trail=money_trail_out,
        feasibility=primary_feasibility_out,
        geojson_risk_layer=geojson_layer,
        risk_score=risk_score,
        risk_tier=risk_tier,
    )



# ─────────────────────────────────────────────
# HELPER: crude lat/lon → city name lookup
# Day 4: replace with PostGIS ST_Within query
# ─────────────────────────────────────────────
_CITY_BOUNDS = {
    "Mumbai":    (18.87, 19.27, 72.77, 72.99),
    "Delhi":     (28.40, 28.88, 76.84, 77.35),
    "Bangalore": (12.83, 13.14, 77.46, 77.78),
    "Hyderabad": (17.28, 17.55, 78.35, 78.60),
    "Chennai":   (12.90, 13.23, 80.15, 80.30),
    "Kolkata":   (22.45, 22.65, 88.30, 88.48),
    "Pune":      (18.43, 18.63, 73.77, 73.97),
    "Ahmedabad": (22.95, 23.12, 72.53, 72.68),
    "Jaipur":    (26.83, 26.98, 75.74, 75.90),
    "Lucknow":   (26.78, 26.96, 80.87, 81.05),
}

def _infer_city(lat: Optional[float], lon: Optional[float]) -> str:
    if lat is None or lon is None:
        return "Unknown"
    for city, (lat_min, lat_max, lon_min, lon_max) in _CITY_BOUNDS.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return city
    return "Unknown"
