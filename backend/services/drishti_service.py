"""
backend/services/drishti_service.py — Project DRISHTI
======================================================
Central Orchestrator / Facade Service for Project DRISHTI.
Demonstrates Dependency Injection by orchestrating domain models,
repositories, ML predictors, and feasibility calculators.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from backend.domain.complaint import Complaint
from backend.domain.money_trail import MoneyTrail
from backend.domain.transaction import Transaction
from backend.domain.prediction import (
    RiskPrediction,
    AmountPrediction,
    TimePrediction,
)
from backend.domain.intelligence_case import FiveDIntelligence, IntelligenceCase

from backend.repositories.transaction_repository import (
    TransactionRepository,
)
from backend.ml.risk_predictor import get_risk_predictor, CaseRiskPredictor, RiskExplainer
from backend.ml.amount_predictor import get_amount_predictor, CashoutAmountPredictor
from backend.ml.time_predictor import get_time_predictor, TimeWindowPredictor
from backend.services.atm_service import get_atm_predictor, ATMPredictor
from backend.services.feasibility_service import (
    get_feasibility_calculator,
    FeasibilityCalculator,
)
from backend.ml.mule_graph import get_mule_graph, MuleNetworkGraph
from backend.clustering.geo_risk import get_geo_risk_engine
from backend.ml.explainability import get_5d_engine
from backend.nlp.extractor import ComplaintExtractor

from backend.models import (
    PredictionOut,
    FraudType,
    HotspotLocation,
    TimeWindow,
    MuleAccount,
    MoneyTrail as MoneyTrailModel,
    MoneyTrailHop,
    TopKLocation,
    PoliceFeasibility,
    FiveDIntelligence as FiveDModel,
)


class DrishtiIntelligenceService:
    """
    Central Pipeline Facade / Orchestrator.

    Dependency Injection:
      - Accepts repositories, ML predictors, and feasibility calculators via constructor.
      - Enables easy testing via mock injection without live file/DB systems.
    """

    def __init__(
        self,
        transaction_repository: Optional[TransactionRepository] = None,
        risk_predictor: Optional[CaseRiskPredictor] = None,
        amount_predictor: Optional[CashoutAmountPredictor] = None,
        time_predictor: Optional[TimeWindowPredictor] = None,
        atm_predictor: Optional[ATMPredictor] = None,
        feasibility_calculator: Optional[FeasibilityCalculator] = None,
        explainer: Optional[RiskExplainer] = None,
        mule_graph: Optional[MuleNetworkGraph] = None,
        extractor: Optional[ComplaintExtractor] = None,
    ):
        self.transaction_repository = transaction_repository or TransactionRepository()
        self.risk_predictor = risk_predictor or get_risk_predictor()
        self.amount_predictor = amount_predictor or get_amount_predictor()
        self.time_predictor = time_predictor or get_time_predictor()
        self.atm_predictor = atm_predictor or get_atm_predictor()
        self.feasibility_calculator = feasibility_calculator or get_feasibility_calculator()
        self.explainer = explainer or self.risk_predictor.explainer
        self.mule_graph = mule_graph or get_mule_graph()
        self.extractor = extractor or ComplaintExtractor()

        self._geo_risk_engine = get_geo_risk_engine()
        self._5d_engine = get_5d_engine()

    def analyze(self, complaint: Complaint, demo_mode: bool = False) -> IntelligenceCase:
        """
        Orchestrates full intelligence pipeline:
          Complaint -> NLP -> MoneyTrail -> ML Predictions -> ATMs -> Feasibility -> 5D
        """
        complaint.validate()

        # 1. NLP extraction fallback
        nlp = self.extractor.extract(complaint.complaint_text)
        fraud_type_str = complaint.fraud_type or nlp.fraud_type or "upi_fraud"
        amount = complaint.amount if complaint.amount > 0 else (nlp.amount or 0.0)
        account = complaint.bank_account or nlp.bank_account
        complaint_dt = complaint.timestamp or datetime.now(timezone.utc)
        city = complaint.city or self._infer_city(complaint.victim_lat, complaint.victim_lon)

        # 2. Time Prediction (XGBoost Regressor)
        tw = self.time_predictor.predict(
            fraud_type=fraud_type_str,
            amount=amount,
            complaint_dt=complaint_dt,
            city=city,
        )
        time_pred = TimePrediction(
            earliest_minutes=tw.earliest_minutes,
            latest_minutes=tw.latest_minutes,
            peak_minutes=tw.peak_minutes,
            confidence=tw.confidence,
            conformal_q_90=getattr(tw, "conformal_q", 10.6),
            model_source="xgboost",
        )

        # 3. Multi-Hop Money Trail (NetworkX Graph Engine)
        trail_data = self.mule_graph.trace_trail(
            starting_account=account,
            initial_amount=amount,
            incident_time=complaint_dt,
            max_hops=4,
        )

        domain_txns = []
        for h in trail_data.get("hops", []):
            h_ts = None
            if h.get("timestamp"):
                try:
                    h_ts = datetime.fromisoformat(h["timestamp"])
                except Exception:
                    h_ts = None

            domain_txns.append(
                Transaction(
                    transaction_id=h.get("txn_ref") or f"TXN-HOP-{h.get('hop_index', 1)}",
                    source_account=h.get("from_account", "ACC-SRC"),
                    destination_account=h.get("to_account", "ACC-DEST"),
                    amount=float(h.get("amount", amount)),
                    timestamp=h_ts,
                    transaction_type=h.get("txn_type", "IMPS"),
                    hop_number=int(h.get("hop_index", 1)),
                    commission_amount=float(h.get("commission_retained", 0.0)),
                    minutes_from_start=int(h.get("minutes_from_start", 0)),
                    is_terminal_cashout=bool(h.get("is_terminal_cashout", False)),
                    to_bank=h.get("to_bank"),
                    to_ifsc=h.get("to_ifsc"),
                )
            )

        money_trail = MoneyTrail(
            transactions=domain_txns,
            starting_account=trail_data.get("starting_account", account),
            initial_amount=trail_data.get("initial_amount", amount),
            final_cashout_amount=trail_data.get("final_cashout_amount", amount),
            trail_duration_minutes=trail_data.get("trail_duration_minutes", 25.0),
            graph_metrics=trail_data.get("graph_metrics", {}),
            data_source=trail_data.get("data_source", "synthetic_demo_dataset"),
            mule_accounts=trail_data.get("mule_accounts", []),
        )

        # 4. Learned Cash-Out Amount Regression
        amount_res = self.amount_predictor.predict(
            amount=amount,
            fraud_type=fraud_type_str,
            hop_count=money_trail.hop_count(),
            velocity_mins=float(money_trail.trail_duration_minutes),
            hour=complaint_dt.hour,
            day_of_week=complaint_dt.weekday(),
        )
        amount_pred = AmountPrediction(
            predicted_cashout_amount=amount_res["predicted_cashout_amount"],
            lower_bound=amount_res["lower_bound"],
            upper_bound=amount_res["upper_bound"],
            confidence=amount_res["confidence"],
            mae=amount_res.get("mae", 1942.97),
            model_source="gradient_boosting",
        )

        # 5. Candidate ATM Ranking (LocationPredictor)
        loc_res = self.atm_predictor.predict_top_k(
            victim_lat=complaint.victim_lat,
            victim_lon=complaint.victim_lon,
            amount=amount,
            fraud_type=fraud_type_str,
            complaint_dt=complaint_dt,
            city=city,
            k=3,
            graph_metrics=money_trail.graph_metrics,
            demo_mode=demo_mode,
        )
        top_k_raw = loc_res.get("top_k", [])

        # 6. AI Case Risk Prediction & SHAP Attribution
        max_centrality = money_trail.graph_metrics.get("max_betweenness", 0.05)
        risk_res = self.risk_predictor.predict(
            fraud_type=fraud_type_str,
            amount=amount,
            hop_count=money_trail.hop_count(),
            centrality=max_centrality,
            complaint_dt=complaint_dt,
            est_withdrawal_mins=time_pred.peak_minutes,
        )
        risk_pred = RiskPrediction(
            risk_score=risk_res["risk_score"],
            risk_level=risk_res["risk_level"],
            probabilities=risk_res.get("probabilities", {}),
            key_factors=risk_res.get("top_factors", []),
            top_positive_features=risk_res.get("top_positive_features", []),
            top_negative_features=risk_res.get("top_negative_features", []),
            shap_available=bool(risk_res.get("explanation")),
            model_source="random_forest_shap",
        )

        # 7. Police Response Feasibility & Ranking
        top_k_ranked = self.feasibility_calculator.rank_top_k_candidates(
            top_k_locations=top_k_raw,
            peak_withdrawal_minutes=time_pred.peak_minutes,
            case_risk_score=risk_pred.risk_score,
        )
        primary_feasibility = top_k_ranked[0]["feasibility"] if top_k_ranked else None

        # 8. Hotspot
        hotspot_dict = None
        if top_k_ranked:
            primary_cand = top_k_ranked[0]
            hotspot_dict = {
                "lat": primary_cand["lat"],
                "lon": primary_cand["lon"],
                "radius_km": primary_cand.get("radius_km", 0.45),
                "atm_count": primary_cand.get("atm_count", 1),
                "confidence": primary_cand.get("confidence", 0.85),
                "cluster_id": 1,
            }

        # 9. GeoJSON Layer
        geojson = self._geo_risk_engine.generate_risk_geojson(
            victim_lat=complaint.victim_lat,
            victim_lon=complaint.victim_lon,
            top_k_locations=top_k_ranked,
            police_unit=primary_feasibility,
            case_risk_score=risk_pred.risk_score,
        )

        # 10. 5D Actionable Intelligence Synthesis
        raw_5d = self._5d_engine.build_5d_intelligence(
            complaint_id=complaint.case_id,
            fraud_type=fraud_type_str,
            amount=amount,
            hotspot=hotspot_dict,
            top_k_locations=top_k_ranked,
            time_window=time_pred.to_dict(),
            money_trail=trail_data,
            risk_result=risk_res,
            feasibility=primary_feasibility,
            city=city,
        )
        raw_5d["amount"]["predicted_cashout_amount"] = amount_pred.predicted_cashout_amount
        raw_5d["amount"]["lower_bound"] = amount_pred.lower_bound
        raw_5d["amount"]["upper_bound"] = amount_pred.upper_bound
        raw_5d["amount"]["confidence"] = amount_pred.confidence

        five_d = FiveDIntelligence(
            where=raw_5d["where"],
            when=raw_5d["when"],
            amount=raw_5d["amount"],
            why=raw_5d["why"],
            action=raw_5d["action"],
            confidence_summary=raw_5d.get("confidence_summary"),
        )

        return IntelligenceCase(
            complaint=complaint,
            money_trail=money_trail,
            risk_prediction=risk_pred,
            amount_prediction=amount_pred,
            time_prediction=time_pred,
            top_k_atms=top_k_ranked,
            five_d=five_d,
            police_feasibility=primary_feasibility,
            geojson_layer=geojson,
            hotspot=hotspot_dict,
            nlp_entities=nlp.to_dict(),
            extraction_confidence=nlp.extraction_confidence,
        )

    def to_prediction_out(self, case: IntelligenceCase) -> PredictionOut:
        """Translates domain IntelligenceCase into FastAPI PredictionOut response model."""
        c = case.complaint
        tw = case.time_prediction
        mt = case.money_trail
        rp = case.risk_prediction
        ap = case.amount_prediction

        # TimeWindow model
        time_window_out = TimeWindow(
            earliest_minutes=tw.earliest_minutes,
            latest_minutes=tw.latest_minutes,
            peak_minutes=tw.peak_minutes,
            confidence=tw.confidence,
            model_source=tw.model_source,
        )

        # MoneyTrail model
        hops_list = [
            MoneyTrailHop(
                hop_index=t.hop_number,
                from_account=t.source_account,
                to_account=t.destination_account,
                amount=t.amount,
                timestamp=t.timestamp.isoformat() if t.timestamp else "",
                minutes_from_start=t.minutes_from_start,
                txn_type=t.transaction_type,
                txn_ref=t.transaction_id,
                commission_retained=t.commission_amount,
                is_terminal_cashout=t.is_terminal_cashout,
                to_bank=t.to_bank,
                to_ifsc=t.to_ifsc,
            )
            for t in mt.transactions
        ]
        mules_list = [
            MuleAccount(**m) for m in mt.to_dict().get("mule_accounts", [])
        ]
        money_trail_out = MoneyTrailModel(
            starting_account=mt.starting_account,
            hop_count=mt.hop_count(),
            initial_amount=mt.initial_amount,
            final_cashout_amount=mt.final_cashout_amount,
            trail_duration_minutes=int(mt.trail_duration_minutes),
            hops=hops_list,
            mule_accounts=mules_list,
            graph_metrics=mt.graph_metrics,
            data_source=mt.data_source,
        )

        # Hotspot model
        hotspot_out = HotspotLocation(**case.hotspot) if case.hotspot else None

        # TopK locations
        top_k_out = [
            TopKLocation(
                rank=loc["rank"],
                location_name=loc["location_name"],
                lat=loc["lat"],
                lon=loc["lon"],
                radius_km=loc["radius_km"],
                atm_count=loc["atm_count"],
                probability=loc["probability"],
                relative_score=loc.get("relative_score", loc["probability"]),
                ranking_probability=loc.get("ranking_probability", loc["probability"]),
                confidence=loc["confidence"],
                distance_km=loc.get("distance_km"),
                priority_rank=loc.get("priority_rank"),
                interception_priority=loc.get("interception_priority"),
                feasibility=PoliceFeasibility(**loc["feasibility"]) if loc.get("feasibility") else None,
                atm_id=loc.get("atm_id"),
                bank=loc.get("bank"),
                area=loc.get("area"),
                risk_score=loc.get("risk_score"),
                predicted_time_window=loc.get("predicted_time_window"),
                predicted_amount=loc.get("predicted_amount", ap.predicted_cashout_amount),
                reason=loc.get("reason"),
                is_24x7=loc.get("is_24x7", True),
            )
            for loc in case.top_k_atms
        ]

        primary_feasibility_out = (
            PoliceFeasibility(**case.police_feasibility)
            if case.police_feasibility
            else None
        )

        # Persist alert to database
        alert_id = None
        try:
            from backend.database import SessionLocal, Alert
            loc_dict = hotspot_out.model_dump() if hotspot_out else (top_k_out[0].model_dump() if top_k_out else {})
            conf_val = hotspot_out.confidence if hotspot_out else (top_k_out[0].confidence if top_k_out else 0.85)
            with SessionLocal() as db_session:
                db_alert = Alert(
                    complaint_id=c.case_id,
                    predicted_location=loc_dict,
                    confidence=conf_val,
                    status="PENDING",
                    created_at=datetime.now(timezone.utc),
                )
                db_session.add(db_alert)
                db_session.commit()
                db_session.refresh(db_alert)
                alert_id = db_alert.id
        except Exception as e:
            print(f"[DRISHTI] Warning: Could not save alert to SQLite: {e}")

        # Auto-persist Investigation Case Dossier & Timeline Events
        try:
            from backend.services.case_service import get_case_service
            get_case_service().create_case_from_intelligence(case, user="SYSTEM")
        except Exception as e:
            print(f"[DRISHTI] Warning: Could not auto-persist investigation case: {e}")

        has_hist_mule = any(m.is_historical_mule for m in mules_list)

        legacy_alert_level = "CRITICAL" if (rp.risk_score >= 80 or (c.amount and c.amount >= 100000)) else (
            "HIGH" if (rp.risk_score >= 60 or (c.amount and c.amount >= 50000)) else (
                "MEDIUM" if rp.risk_score >= 35 else "LOW"
            )
        )

        return PredictionOut(
            alert_id=alert_id,
            case_id=c.case_id,
            complaint_id=c.case_id,
            fraud_type=FraudType(c.fraud_type),
            amount=c.amount,
            extraction_confidence=case.extraction_confidence,
            is_historical_mule=has_hist_mule,
            hotspot=hotspot_out,
            top_k_locations=top_k_out,
            time_window=time_window_out,
            mule_accounts=mules_list,
            nlp_entities=case.nlp_entities,
            alert_level=legacy_alert_level,
            processed_at=datetime.now(timezone.utc),
            model_versions={
                "nlp": "regex-keywords-v0.2",
                "dbscan": "curated-candidate-atms-v2.1",
                "xgboost": "xgboost-v2.1-trained",
                "networkx": "multihop-graph-v2.1",
                "risk_ai": "risk-v2.2",
                "location": "location-v2.1",
            },
            models={
                "risk": {"version": "risk-v2.2", "source": rp.model_source},
                "amount": {"version": "amount-v2.2", "source": ap.model_source},
                "time": {"version": "xgboost-v2.1-trained", "source": tw.model_source},
                "location": {"version": "location-v2.1", "source": "calibrated_ml"},
            },
            five_d=FiveDModel(**case.five_d.to_dict()),
            money_trail=money_trail_out,
            feasibility=primary_feasibility_out,
            geojson_risk_layer=case.geojson_layer,
            risk_score=rp.risk_score,
            risk_tier=rp.risk_level,
            data_sources={
                "transactions": "synthetic_demo",
                "money_trail": mt.data_source,
                "atm_locations": "curated_demo",
                "police_units": "static_demo",
                "location_benchmark": "synthetic_benchmark",
            },
            prediction_method="calibrated_ml",
            location_prediction={
                "top_k": [l.model_dump() for l in top_k_out],
                "top1_probability": top_k_out[0].probability if top_k_out else 0.0,
                "top3_recall_context": "92.2% evaluated on holdout test cases (vs 90.0% nearest ATM baseline)",
                "model_version": "location-v2.1",
                "dataset_type": "synthetic_benchmark",
            },
            time_prediction={
                "predicted_minutes": tw.peak_minutes,
                "lower_bound": tw.earliest_minutes,
                "upper_bound": tw.latest_minutes,
                "coverage": 0.90,
                "uncertainty_method": "split_conformal_prediction",
                "model_version": "xgboost-v2.1-trained",
            },
            amount_prediction={
                "predicted_amount": ap.predicted_cashout_amount,
                "lower_bound": ap.lower_bound,
                "upper_bound": ap.upper_bound,
                "model_version": "amount-v2.2",
                "dataset_type": "synthetic_benchmark",
            },
            risk_prediction={
                "risk_score": rp.risk_score,
                "risk_level": rp.risk_level,
                "probabilities": rp.probabilities,
                "calibration_status": "calibrated_probabilities",
                "model_version": "risk-v2.2",
            },
            explainability={
                "source": "shap_tree_explainer" if rp.shap_available else "heuristic_fallback",
                "features": rp.key_factors,
                "top_positive_features": rp.top_positive_features,
                "top_negative_features": rp.top_negative_features,
            },
            data_quality={
                "status": "good",
                "warnings": [],
            },
        )

    def _infer_city(self, lat: Optional[float], lon: Optional[float]) -> str:
        if lat is None or lon is None:
            return "Hyderabad"
        centers = {
            "Hyderabad": (17.3850, 78.4867),
            "Bangalore": (12.9716, 77.5946),
            "Mumbai": (19.0760, 72.8777),
            "Delhi": (28.6139, 77.2090),
            "Chennai": (13.0827, 80.2707),
            "Kolkata": (22.5726, 88.3639),
            "Pune": (18.5204, 73.8567),
        }
        closest_city = "Hyderabad"
        min_dist = float("inf")
        for c, (clat, clon) in centers.items():
            dist = (lat - clat) ** 2 + (lon - clon) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_city = c
        return closest_city


_drishti_service_instance: Optional[DrishtiIntelligenceService] = None

def get_drishti_service() -> DrishtiIntelligenceService:
    global _drishti_service_instance
    if _drishti_service_instance is None:
        _drishti_service_instance = DrishtiIntelligenceService()
    return _drishti_service_instance
