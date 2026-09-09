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

from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.health   import router as health_router
from backend.routes.predict  import router as predict_router
from backend.routes.feedback import router as feedback_router
from backend.routes.simulation import router as simulation_router
from backend.routes.auth     import router as auth_router
from backend.routes.cases    import router as cases_router
from backend.routes.audit    import router as audit_router
from backend.database        import init_db, init_users, init_demo_cases


# ─────────────────────────────────────────────
# LIFESPAN CONTEXT MANAGER
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup pre-warming and graceful shutdown.
    Pre-warms ML singletons so the first request doesn't cold-start.
    """
    # Initialize SQLite database tables
    init_db()

    # Create demo user accounts if no users exist (first-time setup)
    init_users()

    # Seed 5 deterministic investigation demo cases if empty
    init_demo_cases()

    # Pre-warm XGBoost predictor
    from backend.routes.predict import _get_time_model
    _get_time_model()

    # Pre-warm Risk Predictor & SHAP Explainer
    from backend.ml.risk_predictor import get_risk_predictor
    from backend.ml.mule_graph import get_mule_graph
    from backend.ml.feasibility import get_feasibility_engine
    rp = get_risk_predictor()
    try:
        rp._get_explainer()
    except Exception:
        pass
    get_mule_graph()
    get_feasibility_engine()

    # Pre-warm Location & Amount Predictors
    from backend.ml.location_predictor import get_location_predictor
    from backend.ml.amount_predictor import get_amount_predictor
    get_location_predictor()
    get_amount_predictor()

    yield

    print("[DRISHTI] API shutting down.")


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
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# CORS
# Allow the React frontend (localhost:3000 during dev) to call the API.
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────

app.include_router(auth_router)            # POST /auth/login, /auth/logout, GET /auth/me
app.include_router(health_router)          # GET /health, /ready, /system/status
app.include_router(predict_router)         # POST /predict
app.include_router(cases_router)           # /cases (CRUD, timeline, outcome evaluation, candidate retrain)
app.include_router(audit_router)           # /audit-logs (Security & investigation audit)
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
