"""
backend/ml/explainability.py — Project DRISHTI
================================================
Explainable AI (XAI) & "5D Intelligence" Synthesis Engine.

Transforms all pipeline components into the 5 explicit intelligence dimensions:
  1. WHERE  — Ranked cash-out clusters, search perimeters, and location metadata.
  2. WHEN   — Predicted minutes-to-withdrawal window and operational urgency status.
  3. AMOUNT — Incident fraud amount, multi-hop trail value, and estimated cash-out.
  4. WHY    — Plain-English narrative explanation and key ML signal attributions.
  5. ACTION — Concrete, actionable law enforcement standard operating procedure (SOP).
"""

from typing import Dict, Any, List, Optional


class FiveDIntelligenceEngine:
    """
    Synthesizes multi-model predictions into structured, explainable 5D intelligence.
    """

    def build_5d_intelligence(
        self,
        complaint_id: str,
        fraud_type: str,
        amount: float,
        hotspot: Optional[Dict[str, Any]],
        top_k_locations: List[Dict[str, Any]],
        time_window: Optional[Dict[str, Any]],
        money_trail: Dict[str, Any],
        risk_result: Dict[str, Any],
        feasibility: Optional[Dict[str, Any]],
        city: str = "Unknown",
    ) -> Dict[str, Any]:
        """
        Synthesizes the complete 5D Intelligence payload.
        """
        # ─────────────────────────────────────────────
        # 1. WHERE
        # ─────────────────────────────────────────────
        primary_loc = top_k_locations[0] if top_k_locations else (hotspot or {})
        where_dim = {
            "primary_location_name": primary_loc.get("location_name", "Identified ATM Cluster"),
            "primary_coordinates": {
                "lat": primary_loc.get("lat", 0.0),
                "lon": primary_loc.get("lon", 0.0),
            },
            "search_radius_km": primary_loc.get("radius_km", 0.5),
            "atm_count_in_zone": primary_loc.get("atm_count", 1),
            "city": city,
            "candidate_count": len(top_k_locations),
            "top_candidates": [
                {
                    "rank": loc.get("rank", i + 1),
                    "name": loc.get("location_name", f"Candidate #{i+1}"),
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon"),
                    "probability": loc.get("probability", 0.5),
                    "confidence": loc.get("confidence", 0.5),
                    "priority_rank": loc.get("priority_rank", i + 1),
                    "distance_km": loc.get("distance_km", 1.0),
                }
                for i, loc in enumerate(top_k_locations)
            ],
        }

        # ─────────────────────────────────────────────
        # 2. WHEN
        # ─────────────────────────────────────────────
        earliest = time_window.get("earliest_minutes", 20) if time_window else 20
        peak = time_window.get("peak_minutes", 35) if time_window else 35
        latest = time_window.get("latest_minutes", 60) if time_window else 60
        tw_conf = time_window.get("confidence", 0.75) if time_window else 0.50

        if peak <= 25:
            urgency = "CRITICAL_WINDOW"
            countdown = f"High-velocity cash-out predicted within {earliest}–{peak} mins!"
        elif peak <= 45:
            urgency = "HIGH_PRIORITY"
            countdown = f"Standard cyber-mule cash-out window: peak in ~{peak} mins ({earliest}–{latest} min range)"
        else:
            urgency = "STANDARD_SURVEILLANCE"
            countdown = f"Extended withdrawal window: {earliest}–{latest} mins (peak ~{peak} min)"

        when_dim = {
            "earliest_minutes": earliest,
            "peak_minutes": peak,
            "latest_minutes": latest,
            "confidence": tw_conf,
            "urgency_status": urgency,
            "operational_countdown": countdown,
        }

        # ─────────────────────────────────────────────
        # 3. AMOUNT
        # ─────────────────────────────────────────────
        trail_val = money_trail.get("initial_amount", amount)
        final_cashout = money_trail.get("final_cashout_amount", amount)
        hop_count = money_trail.get("hop_count", 1)

        amount_dim = {
            "reported_fraud_amount": amount,
            "formatted_reported": f"₹{int(amount):,}",
            "total_trail_volume": trail_val,
            "formatted_trail": f"₹{int(trail_val):,}",
            "estimated_cashout_amount": final_cashout,
            "formatted_cashout": f"₹{int(final_cashout):,}",
            "currency": "INR",
            "layering_commission_lost": round(trail_val - final_cashout, 2),
            "trail_hop_count": hop_count,
        }

        # ─────────────────────────────────────────────
        # 4. WHY (Explainability / Rationale)
        # ─────────────────────────────────────────────
        risk_score = risk_result.get("risk_score", 50.0)
        risk_level = risk_result.get("risk_level", "MEDIUM")
        top_factors = risk_result.get("top_factors", [])

        # Formulate a clear natural-language rationale for officers & judges
        factor_phrases = []
        if amount >= 50000:
            factor_phrases.append(f"high-value transaction (₹{int(amount):,})")
        if hop_count >= 3:
            factor_phrases.append(f"deliberate {hop_count}-hop syndicate layering")
        elif hop_count == 2:
            factor_phrases.append("secondary mule transfer")

        flagged_mules = money_trail.get("mule_accounts", [])
        if flagged_mules and flagged_mules[0].get("centrality", 0.0) > 0.05:
            factor_phrases.append("transit account with high network betweenness centrality")

        if peak <= 35:
            factor_phrases.append(f"compressed withdrawal window ({peak} min peak)")

        factors_summary = ", ".join(factor_phrases) if factor_phrases else "transaction velocity anomaly"

        why_summary = (
            f"Flagged as {risk_level} Risk (Score: {risk_score}/100) driven by {factors_summary}. "
            f"DBSCAN spatial clustering localized {primary_loc.get('atm_count', 1)} high-density withdrawal terminals "
            f"within {primary_loc.get('radius_km', 0.5):.2f}km of the victim origin, matching historical {fraud_type.replace('_', ' ').upper()} cash-out trajectories."
        )

        shap_expl = risk_result.get("explanation", [])
        driver_labels = [
            f.get("human_label", f.get("feature", "Risk Factor"))
            for f in shap_expl
        ] if shap_expl else [f["factor"] for f in top_factors]

        why_dim = {
            "summary": why_summary,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "key_drivers": driver_labels,
            "shap_explanation": shap_expl,
            "explanation": shap_expl,
            "factor_attributions": top_factors,
            "syndicate_detected": (hop_count >= 3 or risk_score >= 70),
        }

        # ─────────────────────────────────────────────
        # 5. ACTION (Recommended Investigative Prioritization & Protocol Guidance)
        # ─────────────────────────────────────────────
        unit_name = feasibility.get("unit_name", "Nearest Patrol Unit") if feasibility else "Nearest Interceptor"
        eta_mins = feasibility.get("eta_minutes", 12.0) if feasibility else 12.0
        time_margin = feasibility.get("time_margin_minutes", 15.0) if feasibility else 15.0
        terminal_account = money_trail.get("hops", [{}])[-1].get("to_account", "beneficiary account") if money_trail.get("hops") else "beneficiary account"

        if risk_level in ("CRITICAL", "HIGH") and time_margin >= 0:
            sop_type = "RECOMMENDED_PHYSICAL_INTERCEPTION"
            primary_action = (
                f"RECOMMENDED ACTION: Suggest priority patrol alert for {unit_name} (Estimated transit: {eta_mins} min vs {peak} min estimated peak window) toward {primary_loc.get('location_name')}. "
                f"Establish visual observation on ATM exterior perimeter. Recommended protocol: intercept suspect prior to cash withdrawal."
            )
            secondary_action = (
                f"INVESTIGATIVE GUIDANCE: Recommend manual submission via 1930 / I4C portal for lien marker on beneficiary account {terminal_account}. "
                f"Draft formal Section 91 CrPC / Section 94 BNSS requisition to bank nodal officer for debit freeze."
            )
        elif risk_level in ("CRITICAL", "HIGH") and time_margin < 0:
            sop_type = "RECOMMENDED_ACCOUNT_FREEZE_AND_CCTV"
            primary_action = (
                f"RECOMMENDED PROTOCOL: Recommend urgent manual escalation on 1930 / I4C portal for beneficiary account {terminal_account}. "
                f"Estimated police transit time ({eta_mins} min) exceeds estimated peak cash-out time ({peak} min); recommend prioritizing electronic fund stoppage."
            )
            secondary_action = (
                f"INVESTIGATIVE GUIDANCE: Recommend requesting ATM CCTV surveillance footage and preserving branch transaction logs under Section 91 CrPC / Section 94 BNSS."
            )
        else:
            sop_type = "INTELLIGENCE_SURVEILLANCE"
            primary_action = (
                f"RECOMMENDED PROTOCOL: Monitor beneficiary account {terminal_account} via National Cyber Crime Reporting Portal (NCRP) records. "
                f"Flag for threshold correlation alerts."
            )
            secondary_action = "INVESTIGATIVE GUIDANCE: Correlate with cyber intelligence registry for recurrent syndicate mule associations."

        action_dim = {
            "action_type": sop_type,
            "primary_action": primary_action,
            "secondary_action": secondary_action,
            "dispatch_unit": unit_name,
            "unit_eta_minutes": eta_mins,
            "time_margin_minutes": time_margin,
            "legal_framework": "Investigative Guidance under Section 91 CrPC / Section 94 Bharatiya Nagarik Suraksha Sanhita (BNSS) & 1930 Protocol (Decision-support advisory; non-automated)",
            "urgency_badge": "SUGGEST_DISPATCH" if (risk_level in ("CRITICAL", "HIGH") and time_margin >= 0) else ("SUGGEST_FREEZE" if risk_level in ("CRITICAL", "HIGH") else "MONITOR"),
        }

        return {
            "where": where_dim,
            "when": when_dim,
            "amount": amount_dim,
            "why": why_dim,
            "action": action_dim,
        }


# Singleton
_five_d_engine: Optional[FiveDIntelligenceEngine] = None

def get_5d_engine() -> FiveDIntelligenceEngine:
    global _five_d_engine
    if _five_d_engine is None:
        _five_d_engine = FiveDIntelligenceEngine()
    return _five_d_engine
