"""
backend/repositories/case_repository.py — Project DRISHTI
=========================================================
Repository layer for cybercrime investigation Cases and CaseEvents.
Encapsulates CRUD, filtering, timeline recording, and dashboard metrics aggregation.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from backend.database import SessionLocal, Case, CaseEvent
from backend.domain.case_management import calculate_prediction_accuracy, compute_priority


class CaseRepository:
    """
    Encapsulates persistence and retrieval operations for Case and CaseEvent entities.
    """

    LEGACY_ID_MAP = {
        "DR-2026-1001": "CASE-001-UPI-CRITICAL",
        "DR-2026-1002": "CASE-002-LOWVAL-MEDIUM",
        "DR-2026-1003": "CASE-003-MULE-RING-CRITICAL",
        "DR-2026-1004": "CASE-004-NIGHT-CASHOUT-HIGH",
        "DR-2026-1005": "CASE-005-LEGIT-LOW",
    }

    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def create(self, case_dict: Dict[str, Any]) -> Case:
        """Persists a new investigation case."""
        db: Session = self.session_factory()
        try:
            case = Case(**case_dict)
            db.add(case)
            db.commit()
            db.refresh(case)
            return case
        finally:
            db.close()

    def _resolve_case(self, db: Session, case_id: str) -> Optional[Case]:
        """Helper to resolve a case by ID or legacy alias."""
        if not case_id:
            return None
        clean_id = case_id.strip()
        canonical_id = self.LEGACY_ID_MAP.get(clean_id, clean_id)
        case = db.query(Case).filter(Case.case_id == canonical_id).first()
        if not case and clean_id != canonical_id:
            case = db.query(Case).filter(Case.case_id == clean_id).first()
        return case

    def get_by_id(self, case_id: str) -> Optional[Case]:
        """Finds a case by case_id, supporting canonical IDs with legacy alias fallback."""
        db: Session = self.session_factory()
        try:
            return self._resolve_case(db, case_id)
        finally:
            db.close()

    def get_by_complaint_id(self, complaint_id: str) -> Optional[Case]:
        """Finds a case by complaint_id."""
        if not complaint_id:
            return None
        db: Session = self.session_factory()
        try:
            return db.query(Case).filter(Case.complaint_id == complaint_id.strip()).first()
        finally:
            db.close()

    def list_cases(
        self,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Case]:
        """Lists cases with optional status/risk/search filters, ordered by priority desc."""
        db: Session = self.session_factory()
        try:
            q = db.query(Case)
            if status:
                q = q.filter(Case.status == status.strip().upper())
            if risk_level:
                q = q.filter(Case.risk_level == risk_level.strip().upper())
            if search_query:
                term = f"%{search_query.strip()}%"
                q = q.filter(
                    or_(
                        Case.case_id.ilike(term),
                        Case.complaint_id.ilike(term),
                        Case.predicted_area.ilike(term),
                        Case.assigned_investigator.ilike(term),
                        Case.fraud_type.ilike(term),
                    )
                )
            return q.order_by(desc(Case.priority_score), desc(Case.created_at)).offset(offset).limit(limit).all()
        finally:
            db.close()

    def count_cases(self) -> int:
        """Returns total number of cases."""
        db: Session = self.session_factory()
        try:
            return db.query(Case).count()
        finally:
            db.close()

    def get_stats(self) -> Dict[str, Any]:
        """
        Computes dynamic dashboard KPI metrics from the cases table.
        Does NOT return fake or hardcoded numbers.
        """
        db: Session = self.session_factory()
        try:
            total_cases = db.query(Case).count()
            active_cases = (
                db.query(Case)
                .filter(Case.status.in_(["NEW", "ANALYZING", "HIGH_PRIORITY", "ACTION_REQUIRED", "FIELD_ACTION"]))
                .count()
            )
            critical_cases = db.query(Case).filter(Case.risk_level == "CRITICAL").count()
            high_risk_cases = db.query(Case).filter(Case.risk_level == "HIGH").count()
            action_required_cases = db.query(Case).filter(Case.status == "ACTION_REQUIRED").count()
            field_action_cases = db.query(Case).filter(Case.status == "FIELD_ACTION").count()
            resolved_cases = db.query(Case).filter(Case.status == "RESOLVED").count()
            closed_cases = db.query(Case).filter(Case.status == "CLOSED").count()

            # Prediction accuracy metrics from verified outcomes
            resolved_with_outcome = (
                db.query(Case)
                .filter(Case.outcome.isnot(None), Case.outcome_metrics.isnot(None))
                .all()
            )
            total_evaluated = len(resolved_with_outcome)
            successful_predictions = 0
            location_hits = 0
            time_window_hits = 0

            for c in resolved_with_outcome:
                metrics = c.outcome_metrics or {}
                if metrics.get("overall_success"):
                    successful_predictions += 1
                if metrics.get("location_accuracy") or metrics.get("top_k_hit"):
                    location_hits += 1
                if metrics.get("time_window_accuracy"):
                    time_window_hits += 1

            prediction_accuracy = (
                round((successful_predictions / total_evaluated) * 100.0, 1)
                if total_evaluated > 0
                else None
            )

            return {
                "total_cases": total_cases,
                "active_cases": active_cases,
                "critical_cases": critical_cases,
                "high_risk_cases": high_risk_cases,
                "action_required": action_required_cases,
                "field_action": field_action_cases,
                "resolved": resolved_cases,
                "closed": closed_cases,
                "predictions_generated": total_cases,
                "evaluated_outcomes": total_evaluated,
                "successful_predictions": successful_predictions,
                "prediction_accuracy_pct": prediction_accuracy,
                "location_hit_rate_pct": round((location_hits / total_evaluated) * 100.0, 1) if total_evaluated > 0 else None,
                "time_window_hit_rate_pct": round((time_window_hits / total_evaluated) * 100.0, 1) if total_evaluated > 0 else None,
            }
        finally:
            db.close()

    def update_status(
        self,
        case_id: str,
        status: str,
        user: str = "SYSTEM",
        note: Optional[str] = None,
    ) -> Optional[Case]:
        """Updates case status and writes a timeline event."""
        db: Session = self.session_factory()
        try:
            case = self._resolve_case(db, case_id)
            if not case:
                return None
            old_status = case.status
            case.status = status.strip().upper()
            case.updated_at = datetime.now(timezone.utc)
            if note:
                case.notes = (case.notes + "\n" + note) if case.notes else note

            # Add timeline event
            event = CaseEvent(
                case_id=case.case_id,
                timestamp=datetime.now(timezone.utc),
                event_type="STATUS_CHANGED",
                description=f"Status transitioned from {old_status} to {case.status}." + (f" Note: {note}" if note else ""),
                user=user,
            )
            db.add(event)
            db.commit()
            db.refresh(case)
            return case
        finally:
            db.close()

    def assign_investigator(
        self,
        case_id: str,
        investigator: str,
        user: str = "SYSTEM",
    ) -> Optional[Case]:
        """Assigns an investigator to a case."""
        db: Session = self.session_factory()
        try:
            case = self._resolve_case(db, case_id)
            if not case:
                return None
            case.assigned_investigator = investigator.strip()
            case.updated_at = datetime.now(timezone.utc)

            event = CaseEvent(
                case_id=case.case_id,
                timestamp=datetime.now(timezone.utc),
                event_type="CASE_ASSIGNED",
                description=f"Assigned investigator updated to {investigator.strip()}.",
                user=user,
            )
            db.add(event)
            db.commit()
            db.refresh(case)
            return case
        finally:
            db.close()

    def record_outcome(
        self,
        case_id: str,
        outcome_data: Dict[str, Any],
        user: str = "SYSTEM",
    ) -> Optional[Case]:
        """
        Records actual field outcome, computes evaluation metrics automatically,
        updates case status to RESOLVED, and registers timeline events.
        """
        db: Session = self.session_factory()
        try:
            case = self._resolve_case(db, case_id)
            if not case:
                return None

            case_dict = case.to_dict()
            metrics = calculate_prediction_accuracy(case_dict, outcome_data)

            case.outcome = outcome_data
            case.outcome_metrics = metrics
            case.status = "RESOLVED"
            case.updated_at = datetime.now(timezone.utc)

            # Record outcome event
            event_outcome = CaseEvent(
                case_id=case.case_id,
                timestamp=datetime.now(timezone.utc),
                event_type="ACTUAL_OUTCOME",
                description=(
                    f"Field outcome recorded at {outcome_data.get('actual_atm_id', 'N/A')}. "
                    f"Interception: {outcome_data.get('was_intercepted', False)}. "
                    f"Actual amount: ₹{float(outcome_data.get('actual_amount', 0)):,.2f}."
                ),
                user=user,
                metadata_json=outcome_data,
            )
            db.add(event_outcome)

            # Record automated prediction evaluation event
            event_eval = CaseEvent(
                case_id=case.case_id,
                timestamp=datetime.now(timezone.utc),
                event_type="PREDICTION_EVALUATED",
                description=(
                    f"Accuracy automated check: Location: {'HIT' if metrics['location_accuracy'] else 'MISS'}, "
                    f"Top-K: {'HIT' if metrics['top_k_hit'] else 'MISS'}, "
                    f"Time Window: {'ACCURATE' if metrics['time_window_accuracy'] else 'OUTSIDE'}, "
                    f"Amount Error: ₹{metrics['amount_error']:,.2f}."
                ),
                user="EVALUATION_ENGINE",
                metadata_json=metrics,
            )
            db.add(event_eval)

            db.commit()
            db.refresh(case)
            return case
        finally:
            db.close()

    def add_event(
        self,
        case_id: str,
        event_type: str,
        description: str,
        user: str = "SYSTEM",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CaseEvent:
        """Adds a single timeline event for a case."""
        clean_id = case_id.strip() if case_id else ""
        canonical_id = self.LEGACY_ID_MAP.get(clean_id, clean_id)
        db: Session = self.session_factory()
        try:
            event = CaseEvent(
                case_id=canonical_id,
                timestamp=datetime.now(timezone.utc),
                event_type=event_type.strip().upper(),
                description=description.strip(),
                user=user.strip(),
                metadata_json=metadata,
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event
        finally:
            db.close()

    def get_events(self, case_id: str) -> List[CaseEvent]:
        """Returns chronological list of case events for the timeline, supporting legacy aliases."""
        if not case_id:
            return []
        clean_id = case_id.strip()
        canonical_id = self.LEGACY_ID_MAP.get(clean_id, clean_id)
        db: Session = self.session_factory()
        try:
            events = (
                db.query(CaseEvent)
                .filter(CaseEvent.case_id == canonical_id)
                .order_by(CaseEvent.timestamp.asc(), CaseEvent.id.asc())
                .all()
            )
            if not events and clean_id != canonical_id:
                events = (
                    db.query(CaseEvent)
                    .filter(CaseEvent.case_id == clean_id)
                    .order_by(CaseEvent.timestamp.asc(), CaseEvent.id.asc())
                    .all()
                )
            return events
        finally:
            db.close()

    def update_case_intelligence(
        self,
        case_id: str,
        intel_updates: Dict[str, Any],
        user: str = "SYSTEM",
    ) -> Optional[Case]:
        """
        Persists real ML prediction outputs into the database Case dossier
        and appends an auditable INTELLIGENCE_ANALYZED timeline event.
        """
        db: Session = self.session_factory()
        try:
            case = self._resolve_case(db, case_id)
            if not case:
                return None

            for key, val in intel_updates.items():
                if hasattr(case, key) and key not in ("case_id", "created_at"):
                    setattr(case, key, val)
            case.updated_at = datetime.now(timezone.utc)

            cashout_str = f"₹{case.predicted_cashout_amount:,.2f}" if case.predicted_cashout_amount else "N/A"
            area_str = case.predicted_area or "Target Kiosk"
            event = CaseEvent(
                case_id=case.case_id,
                timestamp=datetime.now(timezone.utc),
                event_type="INTELLIGENCE_ANALYZED",
                description=(
                    f"Executed full DRISHTI predictive pipeline. "
                    f"Forecasted cashout: {cashout_str} at {area_str} "
                    f"(Risk: {case.risk_score}/100 [{case.risk_level}])."
                ),
                user=user,
                metadata_json={
                    "risk_score": case.risk_score,
                    "risk_level": case.risk_level,
                    "predicted_cashout_amount": case.predicted_cashout_amount,
                    "predicted_area": case.predicted_area,
                    "priority_score": case.priority_score,
                },
            )
            db.add(event)
            db.commit()
            db.refresh(case)
            return case
        finally:
            db.close()
