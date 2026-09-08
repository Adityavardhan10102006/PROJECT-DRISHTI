"""
routes/health.py — Project DRISHTI
====================================
GET /health — liveness + readiness check.

Used by:
  - Docker health-check (HEALTHCHECK CMD curl /health)
  - Frontend dashboard to show system status badge
  - Load balancer readiness probe (if deployed to cloud later)
"""

from datetime import datetime
from fastapi import APIRouter
from backend.models import HealthResponse

router = APIRouter(tags=["System"])

APP_VERSION = "0.1.0-day1"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API health check",
    description="Returns API version, timestamp, and status of each ML/DB component.",
)
async def health_check() -> HealthResponse:
    """
    Liveness check — always returns 200 if the server is running.

    Day 2+: Replace component statuses with real checks:
      - database:     try a SELECT 1 against PostgreSQL
      - nlp_model:    check if HingBERT model file is loaded in memory
      - ml_model:     check if XGBoost booster is initialised
      - graph_engine: check if NetworkX graph is populated
    """
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        timestamp=datetime.utcnow(),
        components={
            "database":     "not_connected",   # Day 2: PostgreSQL + PostGIS
            "nlp_model":    "not_loaded",      # Day 2: DistilBERT / HingBERT
            "ml_model":     "not_loaded",      # Day 3: XGBoost
            "graph_engine": "not_loaded",      # Day 3: NetworkX
        },
    )
