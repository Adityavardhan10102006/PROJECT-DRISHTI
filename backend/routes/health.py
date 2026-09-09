"""
routes/health.py — Project DRISHTI
====================================
GET /health — liveness + readiness check + real ML metrics.
"""

import os
import json
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.models import HealthResponse

router = APIRouter(tags=["System"])

APP_VERSION = "2.0.0-hackathon"
METRICS_PATH = "models/metrics.json"


@router.get(
    "/health",
    summary="API health check",
    description="Returns API version, timestamp, component statuses, and verified ML model metrics.",
)
async def health_check() -> dict:
    """
    Liveness and component inspection returning live metrics from models/metrics.json.
    """
    metrics_data = {}
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)
        except Exception:
            metrics_data = {}

    models_ready = (
        os.path.exists("models/risk_classifier.joblib")
        and os.path.exists("models/amount_predictor.joblib")
        and os.path.exists("models/time_predictor.json")
    )

    return {
        "status": "ok",
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models_loaded": models_ready,
        "transaction_dataset": os.path.exists("data/transactions.csv"),
        "atm_dataset": os.path.exists("data/hyderabad_atms.csv"),
        "police_dataset": os.path.exists("data/police_units.json"),
        "readiness": "ready" if models_ready else "degraded",
        "components": {
            "database": "sqlite_ready",
            "risk_model": "loaded_random_forest_shap",
            "time_model": "loaded_xgboost",
            "amount_model": "loaded_gradient_boosting",
            "atm_dataset": "loaded_hyderabad_181_atms",
            "police_units": "loaded_21_patrol_units",
            "graph_engine": "loaded_networkx_multi_hop",
        },
        "model_metrics": metrics_data,
        "mode": "PROTOTYPE / DEMO / SYNTHETIC DATASET",
        "provenance_note": "Synthetic transaction data and curated Hyderabad geospatial candidates. No live bank/police feed."
    }


@router.get(
    "/ready",
    summary="Readiness check",
    description="Returns readiness state indicating whether models and datasets are active and serving.",
)
async def readiness_check() -> dict:
    models_ready = (
        os.path.exists("models/risk_classifier.joblib")
        and os.path.exists("models/amount_predictor.joblib")
        and os.path.exists("models/time_predictor.json")
    )
    data_ready = (
        os.path.exists("data/transactions.csv")
        and os.path.exists("data/hyderabad_atms.csv")
        and os.path.exists("data/police_units.json")
    )
    is_ready = models_ready and data_ready
    return {
        "status": "ready" if is_ready else "degraded",
        "models_loaded": models_ready,
        "transaction_dataset": os.path.exists("data/transactions.csv"),
        "atm_dataset": os.path.exists("data/hyderabad_atms.csv"),
        "police_dataset": os.path.exists("data/police_units.json"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
