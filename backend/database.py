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
from datetime import datetime, timezone, timedelta
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
    if the cases table does not contain CASE-001-UPI-CRITICAL.
    Demonstrates all DRISHTI capabilities out of the box.
    """
    db: Session = SessionLocal()
    try:
        # Check if canonical primary case exists
        canonical_exists = db.query(Case).filter(Case.case_id == "CASE-001-UPI-CRITICAL").first()
        if canonical_exists:
            return  # Already seeded with canonical cases

        # Clear legacy cases if present to avoid dual case numbering
        db.query(CaseEvent).delete()
        db.query(Case).delete()
        db.commit()

        print("[DRISHTI-INIT] Seeding 5 canonical deterministic investigation cases...")
        now = datetime.now(timezone.utc)

        cases_data = [
            {
                "case_id": "CASE-001-UPI-CRITICAL",
                "complaint_id": "CASE-001-UPI",
                "complaint_text": "I was defrauded of Rs 85,000 via a fake electricity bill link on WhatsApp. The money was debited immediately to beneficiary account 987654321012 with IFSC SBIN0001423 via UPI reference 329104829102.",
                "incident_time": now - timedelta(hours=2),
                "fraud_type": "upi_fraud",
                "victim_name": "Suresh Kumar",
                "victim_phone": "+91-98490-XXXXX",
                "victim_lat": 17.4435,
                "victim_lon": 78.3772,
                "city": "Hyderabad",
                "amount": 85000.0,
                "origin_account": "987654321012",
                "destination_accounts": ["ACC-MULE-00163", "ACC-MULE-00102", "ACC-TERM-00092"],
                "risk_score": 88.5,
                "risk_level": "CRITICAL",
                "risk_factors": [
                    {"feature": "Transaction Velocity (<8 min/hop)", "contribution": 24.8, "direction": "INCREASES_RISK"},
                    {"feature": "Amount Size (Rs 85,000)", "contribution": 18.2, "direction": "INCREASES_RISK"},
                    {"feature": "Syndicate Centrality Node", "contribution": 14.5, "direction": "INCREASES_RISK"},
                    {"feature": "Night Window Operation", "contribution": 8.0, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 72473.25,
                "amount_range_lower": 68000.0,
                "amount_range_upper": 78000.0,
                "predicted_time_peak_minutes": 38,
                "predicted_time_earliest_minutes": 27,
                "predicted_time_latest_minutes": 49,
                "conformal_interval_minutes": 10.6,
                "predicted_area": "Banjara Hills / Hitec City",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-HYD-047", "bank": "State Bank of India", "location_name": "SBI ATM — Banjara Hills Rd 12", "lat": 17.4156, "lon": 78.4350, "score": 0.942, "probability": 0.942, "distance_km": 3.8, "time_window": "27–49 min", "feasibility": "HIGH"},
                    {"rank": 2, "atm_id": "ATM-HYD-012", "bank": "HDFC Bank", "location_name": "HDFC ATM — Banjara Hills", "lat": 17.4180, "lon": 78.4390, "score": 0.884, "probability": 0.884, "distance_km": 4.1, "time_window": "27–49 min", "feasibility": "HIGH"},
                    {"rank": 3, "atm_id": "ATM-HYD-089", "bank": "ICICI Bank", "location_name": "ICICI ATM — Jubilee Hills Checkpost", "lat": 17.4280, "lon": 78.4120, "score": 0.791, "probability": 0.791, "distance_km": 4.6, "time_window": "27–49 min", "feasibility": "MEDIUM"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-BANJARA-01",
                    "unit_name": "Blue Colts Rapid 04",
                    "station_name": "Banjara Hills Police Station",
                    "assigned_unit": "Blue Colts Rapid 04",
                    "distance_km": 1.4,
                    "eta_minutes": 3.2,
                    "time_margin_minutes": 34.8,
                    "feasibility_score": 92.5,
                    "feasibility_status": "HIGH",
                    "composite_priority": 91.2,
                },
                "priority_score": 91.2,
                "five_d": {
                    "where": {"primary_location": "SBI ATM — Banjara Hills Rd 12", "lat": 17.4156, "lon": 78.4350, "radius_km": 0.5},
                    "when": {"peak_minutes": 38, "earliest_minutes": 27, "latest_minutes": 49, "window": "27–49 min", "urgency": "HIGH"},
                    "amount": {"predicted_cashout_amount": 72473.25, "lower_bound": 68000.0, "upper_bound": 78000.0, "range": "₹68,000 – ₹78,000"},
                    "why": {"top_reasons": ["Rapid 3-hop money dispersal under 20 mins", "Known layering account sequence ACC-MULE-00163", "High-value threshold exceeded (₹85,000)"]},
                    "action": {
                        "protocol": "Recommended Action: Prioritize SBI ATM Banjara Hills Rd 12. Issue emergency Section 91 CrPC freeze directive on beneficiary account ACC-TERM-00092.",
                        "recommended_steps": [
                            "Prioritize the predicted cash-out location.",
                            "Review associated mule account.",
                            "Verify transaction trail.",
                            "Notify authorized response personnel.",
                            "Follow applicable legal/operational procedures."
                        ]
                    },
                },
                "money_trail": {
                    "initial_amount": 85000.0,
                    "final_cashout_amount": 72473.25,
                    "hops": [
                        {"hop_index": 1, "from_account": "ACC-VIC-9849", "to_account": "ACC-MULE-00163", "amount": 85000.0, "timestamp": (now - timedelta(hours=2)).isoformat(), "txn_type": "UPI", "txn_ref": "UPI329104829102", "is_terminal_cashout": False, "to_bank": "State Bank of India", "dest_lat": 17.4435, "dest_lon": 78.3772},
                        {"hop_index": 2, "from_account": "ACC-MULE-00163", "to_account": "ACC-MULE-00102", "amount": 79050.0, "timestamp": (now - timedelta(minutes=105)).isoformat(), "txn_type": "IMPS", "txn_ref": "TXN-0000002", "is_terminal_cashout": False, "to_bank": "HDFC Bank", "dest_lat": 17.4350, "dest_lon": 78.4010},
                        {"hop_index": 3, "from_account": "ACC-MULE-00102", "to_account": "ACC-TERM-00092", "amount": 72473.25, "timestamp": (now - timedelta(minutes=90)).isoformat(), "txn_type": "ATM_WITHDRAWAL", "txn_ref": "TXN-0000003", "is_terminal_cashout": True, "to_bank": "State Bank of India", "dest_lat": 17.4156, "dest_lon": 78.4350},
                    ]
                },
                "status": "ACTION_REQUIRED",
                "assigned_investigator": "Insp. R. Sharma",
                "notes": "Fast mule cluster detected. Dispatched Blue Colts unit to Banjara Hills location.",
            },
            {
                "case_id": "CASE-002-LOWVAL-MEDIUM",
                "complaint_id": "CASE-002-SUSPICIOUS",
                "complaint_text": "Telegram work from home task scam made me transfer Rs 12000 for VIP rating unlock. Beneficiary account 451298104812 IFSC HDFC0000128.",
                "incident_time": now - timedelta(hours=5),
                "fraud_type": "upi_fraud",
                "victim_name": "Rohan Verma",
                "victim_phone": "+91-94401-XXXXX",
                "victim_lat": 17.4375,
                "victim_lon": 78.4482,
                "city": "Hyderabad",
                "amount": 12000.0,
                "origin_account": "451298104812",
                "destination_accounts": ["ACC-MULE-4412", "ACC-TERM-1190"],
                "risk_score": 62.0,
                "risk_level": "MEDIUM",
                "risk_factors": [
                    {"feature": "Single Intermediary Mule Hop", "contribution": 14.0, "direction": "INCREASES_RISK"},
                    {"feature": "Moderate Financial Exposure (Rs 12,000)", "contribution": 11.2, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 11400.0,
                "amount_range_lower": 10500.0,
                "amount_range_upper": 12000.0,
                "predicted_time_peak_minutes": 45,
                "predicted_time_earliest_minutes": 30,
                "predicted_time_latest_minutes": 60,
                "conformal_interval_minutes": 12.0,
                "predicted_area": "Ameerpet Metro Station Hub",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-HYD-021", "bank": "HDFC Bank", "location_name": "HDFC ATM — Ameerpet Metro", "lat": 17.4368, "lon": 78.4490, "score": 0.842, "probability": 0.842, "distance_km": 0.8, "time_window": "30–60 min", "feasibility": "HIGH"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-AMEERPET-01",
                    "unit_name": "SR Nagar Mobile Patrol",
                    "station_name": "SR Nagar Police Station",
                    "assigned_unit": "SR Nagar Mobile Patrol",
                    "distance_km": 0.9,
                    "eta_minutes": 2.5,
                    "time_margin_minutes": 42.5,
                    "feasibility_score": 85.0,
                    "feasibility_status": "HIGH",
                    "composite_priority": 71.2,
                },
                "priority_score": 71.2,
                "five_d": {
                    "where": {"primary_location": "HDFC ATM — Ameerpet Metro", "lat": 17.4368, "lon": 78.4490, "radius_km": 0.4},
                    "when": {"peak_minutes": 45, "earliest_minutes": 30, "latest_minutes": 60, "window": "30–60 min", "urgency": "MEDIUM"},
                    "amount": {"predicted_cashout_amount": 11400.0, "range": "₹10,500 – ₹12,000"},
                    "why": {"top_reasons": ["Task scam typology match", "High-traffic commercial metro ATM cluster"]},
                    "action": {"protocol": "Decision support alert sent for Ameerpet precinct patrol review. Digital lien request for beneficiary account."},
                },
                "money_trail": {
                    "initial_amount": 12000.0,
                    "final_cashout_amount": 11400.0,
                    "hops": [
                        {"hop_index": 1, "from_account": "ACC-VIC-1204", "to_account": "ACC-MULE-4412", "amount": 12000.0, "timestamp": (now - timedelta(hours=5)).isoformat(), "txn_type": "UPI", "txn_ref": "UPI882910401821", "is_terminal_cashout": False, "to_bank": "HDFC Bank", "dest_lat": 17.4375, "dest_lon": 78.4482},
                        {"hop_index": 2, "from_account": "ACC-MULE-4412", "to_account": "ACC-TERM-1190", "amount": 11400.0, "timestamp": (now - timedelta(hours=4, minutes=45)).isoformat(), "txn_type": "ATM_WITHDRAWAL", "txn_ref": "TXN-0000008", "is_terminal_cashout": True, "to_bank": "HDFC Bank", "dest_lat": 17.4368, "dest_lon": 78.4490},
                    ]
                },
                "status": "HIGH_PRIORITY",
                "assigned_investigator": "Sub-Insp. K. Rao",
                "notes": "Low-value task scam under investigator review.",
            },
            {
                "case_id": "CASE-003-MULE-RING-CRITICAL",
                "complaint_id": "CASE-003-MULE-RING",
                "complaint_text": "Caller claimed SIM card would be blocked for non-KYC. Installed AnyDesk app and lost Rs 145,000 in three immediate transactions. Transferred to account 62019481023 IFSC ICIC0000005.",
                "incident_time": now - timedelta(hours=8),
                "fraud_type": "kyc_fraud",
                "victim_name": "Priyanka Sen",
                "victim_phone": "+91-98850-XXXXX",
                "victim_lat": 17.4156,
                "victim_lon": 78.4350,
                "city": "Hyderabad",
                "amount": 145000.0,
                "origin_account": "62019481023",
                "destination_accounts": ["ACC-MULE-5521", "ACC-MULE-6619", "ACC-CASHOUT-1120"],
                "risk_score": 94.0,
                "risk_level": "CRITICAL",
                "risk_factors": [
                    {"feature": "Multi-Hop Syndicate (4 Layering Hops)", "contribution": 31.2, "direction": "INCREASES_RISK"},
                    {"feature": "Commission Shaving (5% per hop)", "contribution": 22.0, "direction": "INCREASES_RISK"},
                    {"feature": "High Value (Rs 1,45,000)", "contribution": 19.5, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 131000.0,
                "amount_range_lower": 125000.0,
                "amount_range_upper": 140000.0,
                "predicted_time_peak_minutes": 50,
                "predicted_time_earliest_minutes": 35,
                "predicted_time_latest_minutes": 65,
                "conformal_interval_minutes": 14.0,
                "predicted_area": "Banjara Hills / Somajiguda",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-HYD-047", "bank": "State Bank of India", "location_name": "SBI ATM — Banjara Hills Rd 12", "lat": 17.4156, "lon": 78.4350, "score": 0.955, "probability": 0.955, "distance_km": 1.2, "time_window": "35–65 min", "feasibility": "HIGH"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-BANJARA-01",
                    "unit_name": "Blue Colts Rapid 04",
                    "station_name": "Banjara Hills Police Station",
                    "assigned_unit": "Blue Colts Rapid 04",
                    "distance_km": 1.4,
                    "eta_minutes": 3.2,
                    "time_margin_minutes": 46.8,
                    "feasibility_score": 93.0,
                    "feasibility_status": "HIGH",
                    "composite_priority": 93.6,
                },
                "priority_score": 93.6,
                "five_d": {
                    "where": {"primary_location": "SBI ATM — Banjara Hills Rd 12", "lat": 17.4156, "lon": 78.4350, "radius_km": 0.4},
                    "when": {"peak_minutes": 50, "earliest_minutes": 35, "latest_minutes": 65, "window": "35–65 min", "urgency": "HIGH"},
                    "amount": {"predicted_cashout_amount": 131000.0, "range": "₹1,25,000 – ₹1,40,000"},
                    "why": {"top_reasons": ["Organized AnyDesk remote takeover", "Multiple intermediary fan-out mule cluster"]},
                    "action": {"protocol": "Recommend patrol intercept at Banjara Hills SBI ATM. Issue emergency Section 91 CrPC notice to beneficiary banks."},
                },
                "money_trail": {
                    "initial_amount": 145000.0,
                    "final_cashout_amount": 131000.0,
                    "hops": [
                        {"hop_index": 1, "from_account": "ACC-VIC-3310", "to_account": "ACC-MULE-5521", "amount": 145000.0, "timestamp": (now - timedelta(hours=8)).isoformat(), "txn_type": "IMPS", "txn_ref": "IMPS99102481023", "is_terminal_cashout": False, "to_bank": "ICICI Bank", "dest_lat": 17.4156, "dest_lon": 78.4350},
                        {"hop_index": 2, "from_account": "ACC-MULE-5521", "to_account": "ACC-MULE-6619", "amount": 137750.0, "timestamp": (now - timedelta(hours=7, minutes=45)).isoformat(), "txn_type": "IMPS", "txn_ref": "TXN-0000012", "is_terminal_cashout": False, "to_bank": "ICICI Bank", "dest_lat": 17.4180, "dest_lon": 78.4390},
                        {"hop_index": 3, "from_account": "ACC-MULE-6619", "to_account": "ACC-CASHOUT-1120", "amount": 131000.0, "timestamp": (now - timedelta(hours=7, minutes=20)).isoformat(), "txn_type": "ATM_WITHDRAWAL", "txn_ref": "TXN-0000013", "is_terminal_cashout": True, "to_bank": "State Bank of India", "dest_lat": 17.4156, "dest_lon": 78.4350},
                    ]
                },
                "status": "FIELD_ACTION",
                "assigned_investigator": "Insp. R. Sharma",
                "notes": "Patrol alerted to Somajiguda/Banjara Hills corridor.",
            },
            {
                "case_id": "CASE-004-NIGHT-CASHOUT-HIGH",
                "complaint_id": "CASE-004-NIGHT-CASHOUT",
                "complaint_text": "Phishing SMS for credit card reward points redemption. Entered NetBanking password and debited Rs 58000 at night. Account 33819401824 IFSC UTIB0000045.",
                "incident_time": now - timedelta(hours=24),
                "fraud_type": "phishing",
                "victim_name": "Ananya Reddy",
                "victim_phone": "+91-97000-XXXXX",
                "victim_lat": 17.4399,
                "victim_lon": 78.4983,
                "city": "Hyderabad",
                "amount": 58000.0,
                "origin_account": "33819401824",
                "destination_accounts": ["ACC-MULE-3301", "ACC-CASHOUT-4402"],
                "risk_score": 78.0,
                "risk_level": "HIGH",
                "risk_factors": [
                    {"feature": "Off-Hour Night Cashout Operation", "contribution": 22.1, "direction": "INCREASES_RISK"},
                    {"feature": "Phishing Credential Harvester", "contribution": 18.5, "direction": "INCREASES_RISK"},
                ],
                "predicted_cashout_amount": 54500.0,
                "amount_range_lower": 52000.0,
                "amount_range_upper": 57000.0,
                "predicted_time_peak_minutes": 35,
                "predicted_time_earliest_minutes": 25,
                "predicted_time_latest_minutes": 45,
                "conformal_interval_minutes": 10.0,
                "predicted_area": "Secunderabad Station Road",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-SEC-014", "bank": "Axis Bank", "location_name": "Axis Bank ATM — Clock Tower", "lat": 17.4412, "lon": 78.4998, "score": 0.895, "probability": 0.895, "distance_km": 0.8, "time_window": "25–45 min", "feasibility": "HIGH"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-SECUNDERABAD-01",
                    "unit_name": "Gopalapuram Mobile 1",
                    "station_name": "Gopalapuram Police Station",
                    "assigned_unit": "Gopalapuram Mobile 1",
                    "distance_km": 0.9,
                    "eta_minutes": 2.5,
                    "time_margin_minutes": 32.5,
                    "feasibility_score": 86.0,
                    "feasibility_status": "HIGH",
                    "composite_priority": 81.2,
                },
                "priority_score": 81.2,
                "five_d": {
                    "where": {"primary_location": "Axis Bank ATM — Clock Tower", "lat": 17.4412, "lon": 78.4998, "radius_km": 0.4},
                    "when": {"peak_minutes": 35, "earliest_minutes": 25, "latest_minutes": 45, "window": "25–45 min", "urgency": "HIGH"},
                    "amount": {"predicted_cashout_amount": 54500.0, "range": "₹52,000 – ₹57,000"},
                    "why": {"top_reasons": ["Night-time off-hour rapid transit", "Station Road 24/7 ATM terminal preference"]},
                    "action": {"protocol": "Recommendation: Notify railway police and Secunderabad patrol units. Issue bank freeze notice."},
                },
                "money_trail": {
                    "initial_amount": 58000.0,
                    "final_cashout_amount": 54500.0,
                    "hops": [
                        {"hop_index": 1, "from_account": "ACC-VIC-5801", "to_account": "ACC-MULE-3301", "amount": 58000.0, "timestamp": (now - timedelta(hours=24)).isoformat(), "txn_type": "NEFT", "txn_ref": "NEFT11029481024", "is_terminal_cashout": False, "to_bank": "Axis Bank", "dest_lat": 17.4399, "dest_lon": 78.4983},
                        {"hop_index": 2, "from_account": "ACC-MULE-3301", "to_account": "ACC-CASHOUT-4402", "amount": 54500.0, "timestamp": (now - timedelta(hours=23, minutes=30)).isoformat(), "txn_type": "ATM_WITHDRAWAL", "txn_ref": "TXN-0000018", "is_terminal_cashout": True, "to_bank": "Axis Bank", "dest_lat": 17.4412, "dest_lon": 78.4998},
                    ]
                },
                "status": "RESOLVED",
                "assigned_investigator": "Insp. P. Varma",
                "outcome": {
                    "actual_atm_id": "ATM-SEC-014",
                    "actual_time": (now - timedelta(hours=23, minutes=20)).isoformat(),
                    "actual_amount": 54500.0,
                    "was_intercepted": True,
                    "is_correct": True,
                    "notes": "Field unit intercepted suspect at Clock Tower ATM. Cash recovered and mule identified.",
                },
                "outcome_metrics": {
                    "location_accuracy": True,
                    "time_window_accuracy": True,
                    "amount_error": 0.0,
                    "top_k_hit": True,
                    "overall_success": True,
                },
                "notes": "Case resolved with suspect interception and recovery.",
            },
            {
                "case_id": "CASE-005-LEGIT-LOW",
                "complaint_id": "CASE-005-LEGIT",
                "complaint_text": "Paid Rs 2800 for wholesale grocery supplies to merchant store via PhonePe QR code. No fraud reported.",
                "incident_time": now - timedelta(hours=48),
                "fraud_type": "upi_fraud",
                "victim_name": "Vikram Joshi",
                "victim_phone": "+91-96111-XXXXX",
                "victim_lat": 17.3616,
                "victim_lon": 78.4747,
                "city": "Hyderabad",
                "amount": 2800.0,
                "origin_account": "119284019283",
                "destination_accounts": ["ACC-MERCHANT-9921"],
                "risk_score": 18.5,
                "risk_level": "LOW",
                "risk_factors": [
                    {"feature": "Verified Retail Merchant Point-of-Sale", "contribution": -24.2, "direction": "DECREASES_RISK"},
                    {"feature": "Low Amount (< Rs 5,000)", "contribution": -16.4, "direction": "DECREASES_RISK"},
                ],
                "predicted_cashout_amount": 2800.0,
                "amount_range_lower": 2500.0,
                "amount_range_upper": 2800.0,
                "predicted_time_peak_minutes": 180,
                "predicted_time_earliest_minutes": 90,
                "predicted_time_latest_minutes": 240,
                "conformal_interval_minutes": 60.0,
                "predicted_area": "Charminar Market Terminal",
                "top_k_atms": [
                    {"rank": 1, "atm_id": "ATM-CHAR-005", "bank": "State Bank of India", "location_name": "SBI ATM — Charminar East", "lat": 17.3620, "lon": 78.4750, "score": 0.420, "probability": 0.420, "distance_km": 0.3, "time_window": "90–240 min", "feasibility": "LOW"},
                ],
                "police_feasibility": {
                    "nearest_unit_id": "UNIT-CHARMINAR-01",
                    "unit_name": "Charminar Traffic/Law & Order",
                    "station_name": "Charminar Police Station",
                    "assigned_unit": "Charminar Patrol 1",
                    "distance_km": 0.4,
                    "eta_minutes": 1.5,
                    "time_margin_minutes": 178.5,
                    "feasibility_score": 45.0,
                    "feasibility_status": "LOW",
                    "composite_priority": 29.1,
                },
                "priority_score": 29.1,
                "five_d": {
                    "where": {"primary_location": "SBI ATM — Charminar East", "lat": 17.3620, "lon": 78.4750, "radius_km": 0.5},
                    "when": {"peak_minutes": 180, "window": "90–240 min", "urgency": "LOW"},
                    "amount": {"predicted_cashout_amount": 2800.0, "range": "₹2,500 – ₹2,800"},
                    "why": {"top_reasons": ["Legitimate merchant payment POS", "Low financial risk, single transaction"]},
                    "action": {"protocol": "Decision support: No operational response required. System archive as legitimate trade transaction."},
                },
                "money_trail": {
                    "initial_amount": 2800.0,
                    "final_cashout_amount": 2800.0,
                    "hops": [
                        {"hop_index": 1, "from_account": "ACC-VIC-2800", "to_account": "ACC-MERCHANT-9921", "amount": 2800.0, "timestamp": (now - timedelta(hours=48)).isoformat(), "txn_type": "UPI", "txn_ref": "UPI102948102830", "is_terminal_cashout": True, "to_bank": "State Bank of India", "dest_lat": 17.3616, "dest_lon": 78.4747},
                    ]
                },
                "status": "CLOSED",
                "assigned_investigator": "Analyst D. Reddy",
                "notes": "Legitimate retail transaction verified. Closed dossier.",
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
