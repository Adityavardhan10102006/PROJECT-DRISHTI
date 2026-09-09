"""
backend/database.py — Project DRISHTI
=====================================
Persistent SQLite Database & SQLAlchemy ORM for Alert Tracking,
Case Management, Investigation Events, and Audit Logging.

Defines the SQLite connection engine, session factory, ORM models:
  - Alert: Historical alert and field dispatch notifications
  - User: Authentication, roles, and credential hashes
  - Case: Comprehensive cybercrime investigation dossier
  - CaseEvent: Chronological event timeline for each investigation
  - AuditLog: Immutable security audit trail
"""

import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    JSON,
    Text,
    Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Load environment variables
load_dotenv()

# Ensure local data directory exists for SQLite storage
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_SQLITE_PATH = os.path.join(DATA_DIR, "drishti.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

# SQLite requires check_same_thread=False for multi-threaded access in FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ─────────────────────────────────────────────
# ALERT MODEL (Legacy / Real-time alerts)
# ─────────────────────────────────────────────
class Alert(Base):
    """
    Alert record representing a cybercrime prediction dispatched for field action.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    complaint_id = Column(String(64), index=True, nullable=False)
    predicted_location = Column(JSON, nullable=True)  # Stores lat, lon, radius, ATM candidates
    confidence = Column(Float, nullable=True)         # Model confidence 0.0 - 1.0
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, DISPATCHED, INTERCEPTED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "alert_id": self.id,
            "complaint_id": self.complaint_id,
            "predicted_location": self.predicted_location,
            "confidence": round(self.confidence, 4) if self.confidence is not None else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────
# INVESTIGATION CASE MODEL
# ─────────────────────────────────────────────
class Case(Base):
    """
    Comprehensive investigation case dossier.
    Tracks a cybercrime complaint from intake through money-trail reconstruction,
    ML predictions, tactical dispatch, and verified field outcome.
    """
    __tablename__ = "cases"

    case_id = Column(String(64), primary_key=True, index=True)
    complaint_id = Column(String(64), index=True, nullable=False)
    complaint_text = Column(Text, nullable=True)
    incident_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fraud_type = Column(String(64), default="upi_fraud", nullable=False)
    victim_name = Column(String(128), default="Citizen Complainant", nullable=True)
    victim_phone = Column(String(32), default="+91-XXXXX-XXXXX", nullable=True)
    victim_lat = Column(Float, nullable=True)
    victim_lon = Column(Float, nullable=True)
    city = Column(String(64), default="Hyderabad", nullable=False)
    amount = Column(Float, default=0.0, nullable=False)
    origin_account = Column(String(64), nullable=True)
    destination_accounts = Column(JSON, nullable=True)
    money_trail = Column(JSON, nullable=True)

    # Predictions & Intelligence
    risk_score = Column(Float, default=50.0, nullable=False)
    risk_level = Column(String(32), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors = Column(JSON, nullable=True)
    predicted_cashout_amount = Column(Float, nullable=True)
    amount_range_lower = Column(Float, nullable=True)
    amount_range_upper = Column(Float, nullable=True)
    predicted_time_peak_minutes = Column(Integer, nullable=True)
    predicted_time_earliest_minutes = Column(Integer, nullable=True)
    predicted_time_latest_minutes = Column(Integer, nullable=True)
    conformal_interval_minutes = Column(Float, nullable=True)
    predicted_area = Column(String(128), nullable=True)
    top_k_atms = Column(JSON, nullable=True)
    police_feasibility = Column(JSON, nullable=True)
    priority_score = Column(Float, default=50.0, nullable=False)  # 0.60 * Risk + 0.40 * Feasibility
    five_d = Column(JSON, nullable=True)

    # Lifecycle & Ownership
    status = Column(String(32), default="NEW", nullable=False)  # NEW, ANALYZING, HIGH_PRIORITY, ACTION_REQUIRED, FIELD_ACTION, RESOLVED, CLOSED
    assigned_investigator = Column(String(64), default="Unassigned", nullable=False)
    outcome = Column(JSON, nullable=True)
    outcome_metrics = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "complaint_id": self.complaint_id,
            "complaint_text": self.complaint_text,
            "incident_time": self.incident_time.isoformat() if self.incident_time else None,
            "fraud_type": self.fraud_type,
            "victim_name": self.victim_name,
            "victim_phone": self.victim_phone,
            "victim_lat": self.victim_lat,
            "victim_lon": self.victim_lon,
            "city": self.city,
            "amount": self.amount,
            "origin_account": self.origin_account,
            "destination_accounts": self.destination_accounts or [],
            "money_trail": self.money_trail or {},
            "risk_score": round(self.risk_score, 1) if self.risk_score is not None else 50.0,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors or [],
            "predicted_cashout_amount": round(self.predicted_cashout_amount, 2) if self.predicted_cashout_amount is not None else None,
            "amount_range_lower": round(self.amount_range_lower, 2) if self.amount_range_lower is not None else None,
            "amount_range_upper": round(self.amount_range_upper, 2) if self.amount_range_upper is not None else None,
            "predicted_time_peak_minutes": self.predicted_time_peak_minutes,
            "predicted_time_earliest_minutes": self.predicted_time_earliest_minutes,
            "predicted_time_latest_minutes": self.predicted_time_latest_minutes,
            "conformal_interval_minutes": self.conformal_interval_minutes,
            "predicted_area": self.predicted_area,
            "top_k_atms": self.top_k_atms or [],
            "police_feasibility": self.police_feasibility or {},
            "priority_score": round(self.priority_score, 1) if self.priority_score is not None else 50.0,
            "five_d": self.five_d or {},
            "status": self.status,
            "assigned_investigator": self.assigned_investigator,
            "outcome": self.outcome,
            "outcome_metrics": self.outcome_metrics,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ─────────────────────────────────────────────
# CASE EVENT TIMELINE MODEL
# ─────────────────────────────────────────────
class CaseEvent(Base):
    """
    Chronological audit event recorded during a case investigation.
    """
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    case_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    event_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    user = Column(String(64), default="SYSTEM", nullable=False)
    metadata_json = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "case_id": self.case_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "description": self.description,
            "user": self.user,
            "metadata": self.metadata_json or {},
        }


# ─────────────────────────────────────────────
# AUDIT LOG MODEL
# ─────────────────────────────────────────────
class AuditLog(Base):
    """
    Security and action audit log for investigator actions and system events.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user = Column(String(64), default="SYSTEM", nullable=False)
    action = Column(String(64), nullable=False)
    case_id = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    result = Column(String(32), default="SUCCESS", nullable=False)
    details = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user": self.user,
            "action": self.action,
            "case_id": self.case_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "result": self.result,
            "details": self.details or {},
        }


# ─────────────────────────────────────────────
# DATABASE HELPERS & INITIALIZERS
# ─────────────────────────────────────────────
def init_db():
    """
    Create all database tables if they do not exist.
    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS semantics.
    """
    from backend.auth.user_model import User  # noqa: F401
    Base.metadata.create_all(bind=engine)


def init_users():
    """
    Create standard role accounts on first-time startup if table is empty.
    """
    from backend.auth.user_model import User
    from backend.auth.security import hash_password

    demo_username = os.getenv("DRISHTI_DEMO_USERNAME", "admin").strip().lower()
    demo_password = os.getenv("DRISHTI_DEMO_PASSWORD", "Drishti@2026")

    db: Session = SessionLocal()
    try:
        users_to_seed = [
            (demo_username, "admin@drishti.local", demo_password, "admin"),
            ("analyst", "analyst@drishti.local", "Analyst@2026", "analyst"),
            ("investigator", "investigator@drishti.local", "Investigate@2026", "investigator"),
        ]
        created_any = False
        for uname, uemail, upass, urole in users_to_seed:
            existing = db.query(User).filter(User.username == uname).first()
            if existing is None:
                print(f"[DRISHTI-AUTH] Creating standard {urole} account '{uname}'")
                db.add(User(
                    username=uname,
                    email=uemail,
                    password_hash=hash_password(upass),
                    role=urole,
                    is_active=True,
                ))
                created_any = True
        if created_any:
            db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[DRISHTI-AUTH] Warning initializing users: {exc}")
    finally:
        db.close()


def init_demo_cases():
    """
    Seeds the 5 canonical deterministic demo cases with timeline events
    if the cases table is empty. Demonstrates all DRISHTI capabilities out of the box.
    """
    db: Session = SessionLocal()
    try:
        count = db.query(Case).count()
        if count > 0:
            return  # Already seeded

        print("[DRISHTI-INIT] Seeding 5 deterministic investigation demo cases...")
        now = datetime.now(timezone.utc)

        cases_data = [
            {
                "case_id": "DR-2026-1001",
                "complaint_id": "CMP-HYD-90124",
                "complaint_text": "Victim received fraudulent WhatsApp message offering electricity bill waiver. Clicked APK link and lost Rs 85,000 via rapid UPI transfers.",
                "incident_time": now - datetime.resolution * 3600 * 2,
                "fraud_type": "upi_fraud",
                "victim_name": "Suresh Kumar",
                "victim_phone": "+91-98490-XXXXX",
                "victim_lat": 17.4435,
                "victim_lon": 78.3772,
                "city": "Hyderabad",
                "amount": 85000.0,
                "origin_account": "ACC-9988221144",
                "destination_accounts": ["ACC-MULE-8812", "ACC-MULE-4491", "ACC-CASHOUT-7731"],
                "risk_score": 88.5,
                "risk_level": "CRITICAL",
                "risk_factors": [
                    {"feature": "Transaction Velocity (<8 min/hop)", "contribution": 24.8, "direction": "INCREASES_RISK"},
                    {"feature": "Amount Size (Rs 85,000)", "contribution": 18.2, "direction": "INCREASES_RISK"},
                    {"feature": "Syndicate Centrality Node", "contribution": 14.5, "direction": "INCREASES_RISK"},
                    {"feature": "Night Window Operation", "contribution": 8.0, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 81500.0,
                "amount_range_lower": 78000.0,
                "amount_range_upper": 85000.0,
                "predicted_time_peak_minutes": 38,
                "predicted_time_earliest_minutes": 27,
                "predicted_time_latest_minutes": 49,
                "conformal_interval_minutes": 10.6,
                "predicted_area": "Banjara Hills, Road No. 12",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-HYD-047", "bank": "State Bank of India", "location_name": "SBI ATM — Banjara Hills Rd 12", "lat": 17.4156, "lon": 78.4350, "score": 0.942, "distance_km": 3.8, "time_window": "27–49 min", "feasibility": "HIGH"},
                    {"rank": 2, "atm_id": "ATM-HYD-012", "bank": "HDFC Bank", "location_name": "HDFC ATM — Banjara Hills", "lat": 17.4180, "lon": 78.4390, "score": 0.884, "distance_km": 4.1, "time_window": "27–49 min", "feasibility": "HIGH"},
                    {"rank": 3, "atm_id": "ATM-HYD-089", "bank": "ICICI Bank", "location_name": "ICICI ATM — Jubilee Hills Checkpost", "lat": 17.4280, "lon": 78.4120, "score": 0.791, "distance_km": 4.6, "time_window": "27–49 min", "feasibility": "MEDIUM"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-BANJARA-01",
                    "unit_name": "Blue Colts Rapid 04",
                    "distance_km": 1.4,
                    "eta_minutes": 3.2,
                    "time_margin_minutes": 34.8,
                    "feasibility_score": 92.5,
                    "feasibility_status": "EXCELLENT_MARGIN",
                    "composite_priority": 91.2,
                },
                "priority_score": 91.2,
                "five_d": {
                    "where": {"primary_location": "SBI ATM — Banjara Hills Rd 12", "lat": 17.4156, "lon": 78.4350, "radius_km": 0.5},
                    "when": {"peak_minutes": 38, "window": "27–49 min", "urgency": "HIGH"},
                    "amount": {"predicted_cashout_amount": 81500.0, "range": "₹78,000 – ₹85,000"},
                    "why": {"top_reasons": ["Rapid 3-hop money dispersal under 20 mins", "Known layering account sequence ACC-MULE-8812", "High-value threshold exceeded"]},
                    "action": {"protocol": "Immediate patrol dispatch to SBI ATM Banjara Hills Rd 12. Issue emergency Section 91 CrPC freeze directive on beneficiary account ACC-CASHOUT-7731."},
                },
                "status": "ACTION_REQUIRED",
                "assigned_investigator": "Insp. R. Sharma",
                "notes": "Fast mule cluster detected. Dispatched Blue Colts unit to Banjara Hills location.",
            },
            {
                "case_id": "DR-2026-1002",
                "complaint_id": "CMP-CYB-88310",
                "complaint_text": "Victim lured into fake part-time Telegram rating scam. Deposited Rs 1,50,000 into corporate current accounts.",
                "incident_time": now - datetime.resolution * 3600 * 5,
                "fraud_type": "investment_scam",
                "victim_name": "Priyanka Sen",
                "victim_phone": "+91-94401-XXXXX",
                "victim_lat": 17.4485,
                "victim_lon": 78.3908,
                "city": "Cyberabad",
                "amount": 150000.0,
                "origin_account": "ACC-1100229988",
                "destination_accounts": ["ACC-MULE-5521", "ACC-MULE-6619", "ACC-MULE-9901", "ACC-CASHOUT-1120"],
                "risk_score": 94.0,
                "risk_level": "CRITICAL",
                "risk_factors": [
                    {"feature": "Multi-Hop Syndicate (4 Layering Hops)", "contribution": 31.2, "direction": "INCREASES_RISK"},
                    {"feature": "Commission Shaving (5% per hop)", "contribution": 22.0, "direction": "INCREASES_RISK"},
                    {"feature": "High Value (Rs 1,50,000)", "contribution": 19.5, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 138000.0,
                "amount_range_lower": 132000.0,
                "amount_range_upper": 145000.0,
                "predicted_time_peak_minutes": 52,
                "predicted_time_earliest_minutes": 40,
                "predicted_time_latest_minutes": 68,
                "conformal_interval_minutes": 14.0,
                "predicted_area": "HITEC City / Cyber Towers",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-CYB-003", "bank": "ICICI Bank", "location_name": "ICICI ATM — HITEC City Cyber Towers", "lat": 17.4504, "lon": 78.3808, "score": 0.961, "distance_km": 1.2, "time_window": "40–68 min", "feasibility": "HIGH"},
                    {"rank": 2, "atm_id": "ATM-CYB-019", "bank": "Axis Bank", "location_name": "Axis Bank ATM — Madhapur Metro", "lat": 17.4385, "lon": 78.3970, "score": 0.872, "distance_km": 2.1, "time_window": "40–68 min", "feasibility": "HIGH"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-MADHAPUR-02",
                    "unit_name": "Cyberabad Patrol Alpha 2",
                    "distance_km": 1.8,
                    "eta_minutes": 4.1,
                    "time_margin_minutes": 47.9,
                    "feasibility_score": 93.5,
                    "feasibility_status": "EXCELLENT_MARGIN",
                    "composite_priority": 93.8,
                },
                "priority_score": 93.8,
                "five_d": {
                    "where": {"primary_location": "ICICI ATM — HITEC City Cyber Towers", "lat": 17.4504, "lon": 78.3808, "radius_km": 0.4},
                    "when": {"peak_minutes": 52, "window": "40–68 min", "urgency": "HIGH"},
                    "amount": {"predicted_cashout_amount": 138000.0, "range": "₹1,32,000 – ₹1,45,000"},
                    "why": {"top_reasons": ["4-hop deliberate syndication with 5% commission shaving", "Known multi-account mule distributor", "Critical loss threshold"]},
                    "action": {"protocol": "Deploy plainclothes unit to ICICI ATM Cyber Towers kiosk. Coordinate with bank nodal officer to place 24-hour lien on intermediary accounts."},
                },
                "status": "FIELD_ACTION",
                "assigned_investigator": "Sub-Insp. K. Rao",
                "notes": "Patrol dispatched to Cyber Towers kiosk. Coordinating with Cyber Crime Cell.",
            },
            {
                "case_id": "DR-2026-1003",
                "complaint_id": "CMP-SEC-77192",
                "complaint_text": "Victim received fake lottery message on Telegram, transferred Rs 42,000 for customs processing.",
                "incident_time": now - datetime.resolution * 3600 * 8,
                "fraud_type": "phishing",
                "victim_name": "Mohammed Farooq",
                "victim_phone": "+91-98850-XXXXX",
                "victim_lat": 17.4399,
                "victim_lon": 78.4983,
                "city": "Secunderabad",
                "amount": 42000.0,
                "origin_account": "ACC-3344556677",
                "destination_accounts": ["ACC-MULE-1029", "ACC-CASHOUT-9941"],
                "risk_score": 72.4,
                "risk_level": "HIGH",
                "risk_factors": [
                    {"feature": "Fan-In Aggregator Account", "contribution": 21.0, "direction": "INCREASES_RISK"},
                    {"feature": "High Betweenness Centrality", "contribution": 17.4, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 39500.0,
                "amount_range_lower": 36000.0,
                "amount_range_upper": 42000.0,
                "predicted_time_peak_minutes": 45,
                "predicted_time_earliest_minutes": 32,
                "predicted_time_latest_minutes": 60,
                "conformal_interval_minutes": 14.0,
                "predicted_area": "Secunderabad Station Road",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-SEC-014", "bank": "Axis Bank", "location_name": "Axis Bank ATM — Clock Tower", "lat": 17.4412, "lon": 78.4998, "score": 0.871, "distance_km": 0.8, "time_window": "32–60 min", "feasibility": "HIGH"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-SECUNDERABAD-01",
                    "unit_name": "Gopalapuram Mobile 1",
                    "distance_km": 0.9,
                    "eta_minutes": 2.5,
                    "time_margin_minutes": 42.5,
                    "feasibility_score": 81.4,
                    "feasibility_status": "EXCELLENT_MARGIN",
                    "composite_priority": 76.0,
                },
                "priority_score": 76.0,
                "five_d": {
                    "where": {"primary_location": "Axis Bank ATM — Clock Tower", "lat": 17.4412, "lon": 78.4998, "radius_km": 0.5},
                    "when": {"peak_minutes": 45, "window": "32–60 min", "urgency": "MEDIUM"},
                    "amount": {"predicted_cashout_amount": 39500.0, "range": "₹36,000 – ₹42,000"},
                    "why": {"top_reasons": ["Aggregator account fan-in behavior", "Secunderabad transit hub location preference"]},
                    "action": {"protocol": "Alert Secunderabad railway and local police outposts. Place hold on destination account ACC-CASHOUT-9941."},
                },
                "status": "HIGH_PRIORITY",
                "assigned_investigator": "Insp. P. Varma",
                "notes": "Aggregator account identified receiving multiple small transfers.",
            },
            {
                "case_id": "DR-2026-1004",
                "complaint_id": "CMP-KUK-66512",
                "complaint_text": "Victim scammed via fake KYC update SMS for SBI Yono. Rs 65,000 siphoned.",
                "incident_time": now - datetime.resolution * 3600 * 24,
                "fraud_type": "kyc_fraud",
                "victim_name": "Ananya Reddy",
                "victim_phone": "+91-97000-XXXXX",
                "victim_lat": 17.4938,
                "victim_lon": 78.3995,
                "city": "Hyderabad",
                "amount": 65000.0,
                "origin_account": "ACC-7788990011",
                "destination_accounts": ["ACC-MULE-3301", "ACC-CASHOUT-4402"],
                "risk_score": 81.0,
                "risk_level": "HIGH",
                "risk_factors": [
                    {"feature": "KYC Typology Match", "contribution": 20.4, "direction": "INCREASES_RISK"},
                    {"feature": "Rapid Hop Dispersal", "contribution": 16.5, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 61000.0,
                "amount_range_lower": 58000.0,
                "amount_range_upper": 64000.0,
                "predicted_time_peak_minutes": 35,
                "predicted_time_earliest_minutes": 25,
                "predicted_time_latest_minutes": 45,
                "conformal_interval_minutes": 10.0,
                "predicted_area": "Kukatpally Housing Board (KPHB)",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-KUK-022", "bank": "HDFC Bank", "location_name": "HDFC Bank ATM — KPHB Phase 1", "lat": 17.4945, "lon": 78.4010, "score": 0.915, "distance_km": 0.6, "time_window": "25–45 min", "feasibility": "HIGH"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-KPHB-01",
                    "unit_name": "KPHB Mobile Patrol",
                    "distance_km": 0.7,
                    "eta_minutes": 2.1,
                    "time_margin_minutes": 32.9,
                    "feasibility_score": 87.2,
                    "feasibility_status": "EXCELLENT_MARGIN",
                    "composite_priority": 83.5,
                },
                "priority_score": 83.5,
                "five_d": {
                    "where": {"primary_location": "HDFC Bank ATM — KPHB Phase 1", "lat": 17.4945, "lon": 78.4010, "radius_km": 0.4},
                    "when": {"peak_minutes": 35, "window": "25–45 min", "urgency": "HIGH"},
                    "amount": {"predicted_cashout_amount": 61000.0, "range": "₹58,000 – ₹64,000"},
                    "why": {"top_reasons": ["Urgent KYC SMS lure pattern", "Target terminal in high-density KPHB commercial hub"]},
                    "action": {"protocol": "Field unit intercepted suspect at KPHB ATM. Cash recovered and account frozen."},
                },
                "status": "RESOLVED",
                "assigned_investigator": "Insp. R. Sharma",
                "outcome": {
                    "actual_atm_id": "ATM-KUK-022",
                    "actual_time": (now - datetime.resolution * 3600 * 23.5).isoformat(),
                    "actual_amount": 60000.0,
                    "was_intercepted": True,
                    "is_correct": True,
                    "notes": "Officer intercepted suspect at predicted HDFC ATM. Total Rs 60,000 cash seized.",
                },
                "outcome_metrics": {
                    "location_accuracy": True,
                    "time_window_accuracy": True,
                    "amount_error": 1000.0,
                    "top_k_hit": True,
                    "overall_success": True,
                },
                "notes": "Case resolved successfully with physical suspect apprehension and fund recovery.",
            },
            {
                "case_id": "DR-2026-1005",
                "complaint_id": "CMP-BEG-44120",
                "complaint_text": "Victim paid Rs 8,500 advance for second-hand phone on OLX, seller disconnected phone.",
                "incident_time": now - datetime.resolution * 3600 * 48,
                "fraud_type": "phishing",
                "victim_name": "Vikram Joshi",
                "victim_phone": "+91-96111-XXXXX",
                "victim_lat": 17.4440,
                "victim_lon": 78.4710,
                "city": "Hyderabad",
                "amount": 8500.0,
                "origin_account": "ACC-5566778899",
                "destination_accounts": ["ACC-SINGLE-1011"],
                "risk_score": 24.5,
                "risk_level": "LOW",
                "risk_factors": [
                    {"feature": "Single Isolated Transfer", "contribution": -15.2, "direction": "DECREASES_RISK"},
                    {"feature": "Low Amount (< Rs 10,000)", "contribution": -12.4, "direction": "DECREASES_RISK"},
                ],
                "predicted_cashout_amount": 8500.0,
                "amount_range_lower": 7500.0,
                "amount_range_upper": 8500.0,
                "predicted_time_peak_minutes": 120,
                "predicted_time_earliest_minutes": 60,
                "predicted_time_latest_minutes": 180,
                "conformal_interval_minutes": 60.0,
                "predicted_area": "Begumpet / Prakash Nagar",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-BEG-008", "bank": "Canara Bank", "location_name": "Canara Bank ATM — Begumpet", "lat": 17.4448, "lon": 78.4725, "score": 0.520, "distance_km": 0.4, "time_window": "60–180 min", "feasibility": "LOW"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-BEGUMPET-01",
                    "unit_name": "Begumpet Police Patrol",
                    "distance_km": 0.5,
                    "eta_minutes": 2.0,
                    "time_margin_minutes": 118.0,
                    "feasibility_score": 50.8,
                    "feasibility_status": "EXCELLENT_MARGIN",
                    "composite_priority": 35.0,
                },
                "priority_score": 35.0,
                "five_d": {
                    "where": {"primary_location": "Canara Bank ATM — Begumpet", "lat": 17.4448, "lon": 78.4725, "radius_km": 0.5},
                    "when": {"peak_minutes": 120, "window": "60–180 min", "urgency": "LOW"},
                    "amount": {"predicted_cashout_amount": 8500.0, "range": "₹7,500 – ₹8,500"},
                    "why": {"top_reasons": ["Non-syndicated peer transfer", "Low financial exposure"]},
                    "action": {"protocol": "Standard portal notice served to beneficiary bank. No tactical interception required."},
                },
                "status": "CLOSED",
                "assigned_investigator": "Analyst D. Reddy",
                "notes": "Low priority isolated fraud. Standard digital notice issued.",
            },
        ]

        for cd in cases_data:
            c = Case(**cd)
            db.add(c)

            # Add rich historical timeline events for each demo case
            events = [
                CaseEvent(
                    case_id=c.case_id,
                    timestamp=c.incident_time,
                    event_type="COMPLAINT_RECEIVED",
                    description=f"Complaint received via National Cyber Crime Reporting Portal (NCRRP). Loss amount: ₹{c.amount:,.2f}.",
                    user="CITIZEN_PORTAL",
                ),
                CaseEvent(
                    case_id=c.case_id,
                    timestamp=c.incident_time,
                    event_type="COMPLAINT_ANALYZED",
                    description=f"NLP extraction completed. Classified as {c.fraud_type.upper()} with entity mapping.",
                    user="NLP_ENGINE",
                ),
                CaseEvent(
                    case_id=c.case_id,
                    timestamp=c.incident_time,
                    event_type="MONEY_TRAIL_RECONSTRUCTED",
                    description=f"NetworkX multi-hop money trail traced. Identified {len(c.destination_accounts or [])} connected laundering accounts.",
                    user="MULE_GRAPH_ENGINE",
                ),
                CaseEvent(
                    case_id=c.case_id,
                    timestamp=c.incident_time,
                    event_type="RISK_PREDICTED",
                    description=f"AI Risk Classifier evaluated case. Score: {c.risk_score}/100 [{c.risk_level}]. SHAP feature attributions cached.",
                    user="RISK_PREDICTOR",
                ),
                CaseEvent(
                    case_id=c.case_id,
                    timestamp=c.incident_time,
                    event_type="CASHOUT_LOCATION_PREDICTED",
                    description=f"XGBoost Location Ranker predicted primary cash-out terminal: {c.predicted_area}.",
                    user="LOCATION_PREDICTOR",
                ),
                CaseEvent(
                    case_id=c.case_id,
                    timestamp=c.incident_time,
                    event_type="POLICE_FEASIBILITY_EVALUATED",
                    description=f"Police transit feasibility assessed. Response margin: {c.police_feasibility.get('time_margin_minutes', 30.0)} min. Priority score: {c.priority_score}.",
                    user="FEASIBILITY_ENGINE",
                ),
                CaseEvent(
                    case_id=c.case_id,
                    timestamp=c.incident_time,
                    event_type="ALERT_GENERATED",
                    description=f"5D Actionable Intelligence package generated. Status updated to {c.status}.",
                    user="DRISHTI_ORCHESTRATOR",
                ),
            ]

            if c.status == "FIELD_ACTION":
                events.append(
                    CaseEvent(
                        case_id=c.case_id,
                        timestamp=c.incident_time,
                        event_type="FIELD_ACTION",
                        description=f"Patrol unit {c.police_feasibility.get('unit_name')} dispatched to surveillance point.",
                        user=c.assigned_investigator,
                    )
                )
            elif c.status == "RESOLVED":
                events.append(
                    CaseEvent(
                        case_id=c.case_id,
                        timestamp=c.incident_time,
                        event_type="FIELD_ACTION",
                        description="Patrol unit dispatched to predicted ATM terminal.",
                        user=c.assigned_investigator,
                    )
                )
                events.append(
                    CaseEvent(
                        case_id=c.case_id,
                        timestamp=c.incident_time,
                        event_type="ACTUAL_OUTCOME",
                        description=f"Suspect apprehended at {c.outcome.get('actual_atm_id')}. Interception verified.",
                        user=c.assigned_investigator,
                    )
                )
                events.append(
                    CaseEvent(
                        case_id=c.case_id,
                        timestamp=c.incident_time,
                        event_type="PREDICTION_EVALUATED",
                        description=f"Automated evaluation completed: Location Accuracy: YES, Top-K Hit: YES, Amount Error: ₹{c.outcome_metrics.get('amount_error'):,.2f}.",
                        user="EVALUATION_ENGINE",
                    )
                )

            for ev in events:
                db.add(ev)

            # Audit log entry for case initialization
            db.add(
                AuditLog(
                    user="SYSTEM",
                    action="CASE_CREATED",
                    case_id=c.case_id,
                    result="SUCCESS",
                    details={"fraud_type": c.fraud_type, "amount": c.amount, "priority": c.priority_score},
                )
            )

        db.commit()
        print("[DRISHTI-INIT] 5 demo investigation cases and timeline events successfully created.")
    except Exception as exc:
        db.rollback()
        print(f"[DRISHTI-INIT] Warning seeding demo cases: {exc}")
    finally:
        db.close()


def get_db():
    """FastAPI dependency for yielding DB sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ensure tables are created and seeded on module load
init_db()
init_users()
init_demo_cases()
