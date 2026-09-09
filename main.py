"""
main.py — Project DRISHTI API Entry Point
==========================================
Run with:
  uvicorn main:app --reload --port 8000

Day 1: Health check + stub /predict
Day 2: Add NLP pipeline startup event, database connection
Day 3: Add ML model loading on startup
Day 4: Add WebSocket for real-time dashboard updates
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.health   import router as health_router
from backend.routes.predict  import router as predict_router
from backend.routes.feedback import router as feedback_router
from backend.routes.simulation import router as simulation_router
from backend.database        import init_db

# ─────────────────────────────────────────────
# APP INSTANCE
# ─────────────────────────────────────────────

app = FastAPI(
    title="Project DRISHTI — 5D Predictive Intelligence Platform",
    description=(
        "**D**etection and **R**eal-time **I**ntelligence for **S**urveillance, "
        "**H**otspot **T**racking, and **I**nterception.\n\n"
        "SIH26184 — Ministry of Home Affairs | Blockchain & Cybersecurity\n\n"
        "Predictive 5D analytics framework: Multi-hop money-trail analysis, "
        "AI risk prediction, Top-K withdrawal hotspots, police feasibility ETA, "
        "and continuous outcome feedback loop."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)

# ─────────────────────────────────────────────
# CORS
# Allow the React frontend (localhost:3000 during dev) to call the API.
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# STARTUP / SHUTDOWN EVENTS
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """
    Called once when the server starts.
    Pre-warms ML singletons so the first request doesn't cold-start.
    """
    print("=" * 60)
    print(" [*] DRISHTI API — 5D Predictive Intelligence Platform Starting")
    print("     Multi-Hop Mule Graph + AI Risk Model + Top-K DBSCAN Live.")
    print("=" * 60)
    
    # Initialize SQLite database tables
    init_db()

    # Pre-warm XGBoost predictor
    from backend.routes.predict import _get_time_model
    _get_time_model()

    # Pre-warm Risk Predictor & Mule Graph
    from backend.ml.risk_predictor import get_risk_predictor
    from backend.ml.mule_graph import get_mule_graph
    from backend.ml.feasibility import get_feasibility_engine
    get_risk_predictor()
    get_mule_graph()
    get_feasibility_engine()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Called when the server is shutting down.
    """
    print("[DRISHTI] API shutting down.")


# ─────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────

app.include_router(health_router)          # GET /health
app.include_router(predict_router)         # POST /predict
app.include_router(feedback_router)        # POST /alerts/{id}/outcome, GET /alerts/feedback/stats
app.include_router(simulation_router)      # POST /api/simulation/start, stop, status


# ─────────────────────────────────────────────
# ROOT REDIRECT
# ─────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "project": "DRISHTI",
        "problem_statement": "SIH26184",
        "ministry": "Ministry of Home Affairs",
        "theme": "Blockchain & Cybersecurity",
        "docs": "/docs",
        "health": "/health",
    }
