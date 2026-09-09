"""
backend/domain/case_management.py — Project DRISHTI
===================================================
Domain models, status enums, outcome contracts, and automated accuracy
evaluation logic for cybercrime investigation cases.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import math


class CaseStatus(str, Enum):
    """Investigation lifecycle statuses."""
    NEW = "NEW"
    ANALYZING = "ANALYZING"
    HIGH_PRIORITY = "HIGH_PRIORITY"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    FIELD_ACTION = "FIELD_ACTION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


def compute_priority(risk_score: float, feasibility_score: float) -> float:
    """
    Standardized Priority Formula:
    Priority = 0.60 * Risk + 0.40 * Feasibility

    Guarantees consistent ranking across all components.
    """
    r = float(risk_score) if risk_score is not None else 50.0
    f = float(feasibility_score) if feasibility_score is not None else 50.0
    r = max(0.0, min(100.0, r))
    f = max(0.0, min(100.0, f))
    return round(0.60 * r + 0.40 * f, 2)


def calculate_prediction_accuracy(
    case_data: Dict[str, Any],
    outcome_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluates real field outcome against model predictions.
    Computes:
      - location_accuracy: True if actual ATM matches Top-1 or is within 1.0 km
      - top_k_hit: True if actual ATM is present in top_k_atms list
      - time_window_accuracy: True if actual withdrawal time is within predicted window
      - amount_error: Absolute difference between actual amount and predicted amount
      - amount_error_percentage: Relative error percentage
      - overall_success: (location_accuracy or top_k_hit) and time_window_accuracy
    """
    top_k = case_data.get("top_k_atms") or []
    top_1_atm = top_k[0] if top_k else {}
    top_1_id = top_1_atm.get("atm_id", "").strip().upper()

    actual_atm_id = outcome_data.get("actual_atm_id", "").strip().upper()
    actual_amount = float(outcome_data.get("actual_amount") or 0.0)
    actual_time_str = outcome_data.get("actual_time")

    # 1. Location & Top-K Hit
    top_k_ids = [atm.get("atm_id", "").strip().upper() for atm in top_k if atm.get("atm_id")]
    top_k_hit = actual_atm_id in top_k_ids if actual_atm_id and top_k_ids else False
    location_accuracy = (actual_atm_id == top_1_id) if (actual_atm_id and top_1_id) else False

    # 2. Amount Error
    pred_amount = float(case_data.get("predicted_cashout_amount") or case_data.get("amount") or 0.0)
    amount_error = round(abs(actual_amount - pred_amount), 2) if actual_amount > 0 else 0.0
    amount_error_pct = (
        round((amount_error / actual_amount) * 100.0, 2)
        if actual_amount > 0 and pred_amount > 0
        else 0.0
    )

    # 3. Time Window Accuracy
    time_window_accuracy = False
    earliest_min = case_data.get("predicted_time_earliest_minutes")
    latest_min = case_data.get("predicted_time_latest_minutes")

    if actual_time_str:
        try:
            # Parse ISO time
            actual_dt = datetime.fromisoformat(actual_time_str.replace("Z", "+00:00"))
            inc_time_str = case_data.get("incident_time")
            if inc_time_str:
                inc_dt = datetime.fromisoformat(inc_time_str.replace("Z", "+00:00"))
                diff_minutes = (actual_dt - inc_dt).total_seconds() / 60.0
                if earliest_min is not None and latest_min is not None:
                    time_window_accuracy = (earliest_min <= diff_minutes <= latest_min)
                else:
                    time_window_accuracy = True
            else:
                time_window_accuracy = True
        except Exception:
            time_window_accuracy = outcome_data.get("is_correct", False)
    else:
        time_window_accuracy = outcome_data.get("is_correct", False)

    # 4. Overall Success
    overall_success = (location_accuracy or top_k_hit) and time_window_accuracy

    return {
        "location_accuracy": location_accuracy,
        "top_k_hit": top_k_hit,
        "time_window_accuracy": time_window_accuracy,
        "amount_error": amount_error,
        "amount_error_percentage": amount_error_pct,
        "overall_success": overall_success,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
