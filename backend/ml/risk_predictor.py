"""
backend/ml/risk_predictor.py — Project DRISHTI
================================================
Inference wrapper for the AI/ML Cybercrime Case Risk Model.

Features:
  - Predicts 0–100 risk score and categorical tier (LOW | MEDIUM | HIGH | CRITICAL)
  - Uses trained RandomForestClassifier from models/risk_classifier.joblib
  - Computes exact feature attributions via shap.TreeExplainer
    for Explainable AI (XAI) output.
  - Safe fallback to heuristic scoring if model file is not yet available.
"""

import os
import json
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import shap

MODEL_PATH = "models/risk_classifier.joblib"
META_PATH = "models/risk_meta.json"

RISK_TIERS = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH",
    3: "CRITICAL",
}

FRAUD_TYPE_MAP = {"upi_fraud": 0, "kyc_fraud": 1, "phishing": 2, "legitimate": 0}

FEATURE_LABELS = {
    "log_amount": ("transaction_amount", "High Transaction Amount", "Fraud value significantly exceeds standard retail baseline"),
    "hop_count": ("hop_count", "Multi-Hop Money Trail", "Multiple intermediary hops indicate coordinated syndicate layering"),
    "betweenness_centrality": ("betweenness_centrality", "Network Transit Hub Mule", "High centrality account connects multiple laundering clusters"),
    "est_withdrawal_mins": ("withdrawal_urgency", "Compressed Cash-Out Window", "Tight timeline leaves minimal window for physical interception"),
    "hour": ("incident_hour", "Unusual Incident Time", "Transaction timing coincides with off-peak evasion hours"),
    "out_degree": ("fan_out_velocity", "Rapid Account Fan-Out", "High outbound connectivity signals automated mule dispersal"),
    "in_degree": ("fan_in_concentration", "High Inbound Convergence", "Multiple fund sources funneled into single terminal account"),
    "is_weekend": ("weekend_indicator", "Weekend Low-Surveillance Period", "Execution during bank branch closure window"),
    "city_tier": ("urban_tier", "Metro Transit Jurisdiction", "High density metropolitan transaction speed"),
    "fraud_type_enc": ("fraud_typology", "Organized Fraud Typology", "Incident signature aligns with organized syndicate playbooks"),
}


class CaseRiskPredictor:
    """
    Evaluates cybercrime case risk using trained Random Forest / Tree models
    and genuine SHAP TreeExplainer feature attributions.
    """

    def __init__(self, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
        self.model = None
        self.explainer = None
        self.meta = {}
        self.feature_cols: List[str] = []
        self.feature_importances: Dict[str, float] = {}

        if os.path.exists(model_path) and os.path.exists(meta_path):
            try:
                self.model = joblib.load(model_path)
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
                self.feature_cols = self.meta.get("feature_cols", [])
                self.feature_importances = self.meta.get("feature_importances", {})
                
                # Initialize SHAP TreeExplainer
                try:
                    self.explainer = shap.TreeExplainer(self.model)
                    print(f"[DRISHTI] SHAP TreeExplainer initialized on {model_path}")
                except Exception as ex_err:
                    print(f"[DRISHTI] Warning: SHAP initialization deferred ({ex_err})")
                    self.explainer = None

                print(f"[DRISHTI] AI Risk Classifier loaded successfully (Accuracy: {self.meta.get('accuracy')})")
            except Exception as e:
                print(f"[DRISHTI] Could not load risk model ({e}), using rule-based fallback.")
                self.model = None
                self.explainer = None

    def _build_feature_row(
        self,
        fraud_type: str,
        amount: float,
        hop_count: int,
        centrality: float,
        in_degree: int,
        out_degree: int,
        complaint_dt: datetime,
        city_tier: int,
        est_withdrawal_mins: int,
    ) -> Dict[str, float]:
        log_amt = float(np.log1p(max(amount, 0.0)))
        hour = complaint_dt.hour
        is_weekend = int(complaint_dt.weekday() >= 5)
        ft_enc = FRAUD_TYPE_MAP.get(fraud_type, 0)

        return {
            "fraud_type_enc": float(ft_enc),
            "log_amount": log_amt,
            "hop_count": float(hop_count),
            "betweenness_centrality": float(centrality),
            "in_degree": float(in_degree),
            "out_degree": float(out_degree),
            "hour": float(hour),
            "is_weekend": float(is_weekend),
            "city_tier": float(city_tier),
            "est_withdrawal_mins": float(est_withdrawal_mins),
        }

    def predict(
        self,
        fraud_type: str,
        amount: float,
        hop_count: int = 2,
        centrality: float = 0.05,
        in_degree: int = 2,
        out_degree: int = 2,
        complaint_dt: Optional[datetime] = None,
        city_tier: int = 1,
        est_withdrawal_mins: int = 35,
    ) -> Dict[str, Any]:
        """
        Returns:
            {
              "risk_score": float (0-100),
              "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
              "probabilities": dict,
              "top_factors": list of { "feature": str, "description": str, "impact": str }
            }
        """
        if complaint_dt is None:
            complaint_dt = datetime.utcnow()

        feat_dict = self._build_feature_row(
            fraud_type=fraud_type,
            amount=amount,
            hop_count=hop_count,
            centrality=centrality,
            in_degree=in_degree,
            out_degree=out_degree,
            complaint_dt=complaint_dt,
            city_tier=city_tier,
            est_withdrawal_mins=est_withdrawal_mins,
        )

        shap_explanation = []
        df_x = None
        pred_class = 1

        if self.model is not None and self.feature_cols:
            import pandas as pd
            df_x = pd.DataFrame([feat_dict])[self.feature_cols]
            pred_class = int(self.model.predict(df_x)[0])
            pred_probs = self.model.predict_proba(df_x)[0]

            # Weighted expected risk score across class probabilities: [0: 15, 1: 42, 2: 68, 3: 92]
            class_weights = np.array([12.0, 42.0, 68.0, 92.0])
            risk_score = float(np.sum(pred_probs * class_weights))
            risk_score = round(float(np.clip(risk_score, 5.0, 99.0)), 1)

            prob_dict = {
                RISK_TIERS[i]: round(float(pred_probs[i]), 3)
                for i in range(len(pred_probs))
            }
        else:
            # Fallback heuristic calculation
            score = 22.0
            if amount > 50000:
                score += 35
            elif amount > 15000:
                score += 20

            if hop_count >= 3:
                score += 20
            elif hop_count >= 2:
                score += 10

            if centrality > 0.15:
                score += 15

            if est_withdrawal_mins <= 35:
                score += 10

            risk_score = min(98.0, max(8.0, score))
            prob_dict = {"MEDIUM": 0.85}

        # Normalize categorical tier strictly to:
        # 0–25 LOW, 26–50 MEDIUM, 51–75 HIGH, 76–100 CRITICAL
        if risk_score >= 76.0:
            risk_level = "CRITICAL"
        elif risk_score >= 51.0:
            risk_level = "HIGH"
        elif risk_score >= 26.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # ── 1. Calculate Real SHAP Explanations ──
        explanation_source = "heuristic_fallback"
        if self.explainer is not None and df_x is not None:
            shap_explanation = self._compute_shap_explanation(df_x, pred_class, amount, hop_count, centrality)
            if shap_explanation:
                explanation_source = "shap_tree_explainer"

        # Fallback explanation if SHAP failed or model unavailable
        top_factors = self._extract_key_factors(feat_dict, amount, hop_count, centrality, est_withdrawal_mins)
        if not shap_explanation:
            shap_explanation = self._fallback_shap_explanation(top_factors)
            explanation_source = "heuristic_fallback"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "probabilities": prob_dict,
            "explanation": shap_explanation,
            "explanation_source": explanation_source,
            "top_factors": top_factors,
            "model_version": self.meta.get("version", "risk-v2.2"),
            "model_source": "trained_model" if self.model is not None else "heuristic_fallback",
        }

    def _compute_shap_explanation(
        self,
        df_x: Any,
        pred_class: int,
        amount: float,
        hop_count: int,
        centrality: float,
    ) -> List[Dict[str, Any]]:
        """
        Computes exact feature contributions using shap.TreeExplainer.
        Outputs structured items: feature, contribution, direction, badge, human_label, description.
        """
        try:
            sv = self.explainer.shap_values(df_x)
            # Shape for multiclass Random Forest: (1, n_features, n_classes)
            if isinstance(sv, np.ndarray) and sv.ndim == 3:
                class_sv = sv[0, :, pred_class]
            elif isinstance(sv, list) and len(sv) > pred_class:
                class_sv = sv[pred_class][0]
            else:
                class_sv = np.array(sv).flatten()[:len(self.feature_cols)]

            cols = self.feature_cols
            sorted_indices = np.argsort(np.abs(class_sv))[::-1]

            explanation = []
            for idx in sorted_indices[:5]:
                col = cols[idx]
                contrib = float(class_sv[idx])
                clean_name, human_label, default_desc = FEATURE_LABELS.get(
                    col, (col, col.replace("_", " ").title(), "Model feature contribution")
                )

                direction = "increases_risk" if contrib >= 0 else "decreases_risk"
                
                # Visual badge based on risk contribution
                if contrib >= 0.08:
                    badge = "🔴"
                elif contrib >= 0.02:
                    badge = "🟠"
                elif contrib >= 0:
                    badge = "🟡"
                else:
                    badge = "🟢"

                # Tailor descriptions to incident specifics
                if col == "log_amount":
                    desc = f"Reported loss ₹{int(amount):,} is an anomaly driving case severity"
                elif col == "hop_count":
                    desc = f"{hop_count}-hop layering chain indicates organized syndicate evasion"
                elif col == "betweenness_centrality":
                    desc = f"Mule account centrality ({centrality:.3f}) links transit clusters"
                else:
                    desc = default_desc

                explanation.append({
                    "feature": clean_name,
                    "contribution": round(contrib, 4),
                    "direction": direction,
                    "badge": badge,
                    "human_label": human_label,
                    "description": desc,
                })

            return explanation
        except Exception as err:
            print(f"[DRISHTI] Warning: SHAP computation failed ({err}), using fallback.")
            return []

    def _fallback_shap_explanation(
        self, top_factors: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Fallback when SHAP cannot run."""
        out = []
        for tf in top_factors:
            impact = tf.get("impact", "MEDIUM")
            badge = "🔴" if impact == "CRITICAL" else ("🟠" if impact == "HIGH" else "🟡")
            out.append({
                "feature": tf["factor"].lower().replace(" ", "_"),
                "contribution": 0.20 if impact == "CRITICAL" else (0.15 if impact == "HIGH" else 0.08),
                "direction": "increases_risk",
                "badge": badge,
                "human_label": tf["factor"],
                "description": tf["description"],
            })
        return out

    def _extract_key_factors(
        self,
        feat_dict: Dict[str, float],
        amount: float,
        hop_count: int,
        centrality: float,
        est_withdrawal_mins: int,
    ) -> List[Dict[str, str]]:
        factors = []
        if amount >= 50000:
            factors.append({
                "factor": "High Value Fraud",
                "description": f"Fraud amount ₹{int(amount):,} is significantly above the retail threshold.",
                "impact": "HIGH"
            })
        elif amount >= 15000:
            factors.append({
                "factor": "Moderate Value Fraud",
                "description": f"Fraud amount ₹{int(amount):,} warrants priority tracing.",
                "impact": "MEDIUM"
            })

        if hop_count >= 3:
            factors.append({
                "factor": "Deep Multi-Hop Layering",
                "description": f"{hop_count}-tier mule transaction chain indicates coordinated syndicate money flow.",
                "impact": "CRITICAL"
            })
        elif hop_count == 2:
            factors.append({
                "factor": "Two-Hop Mule Transfer",
                "description": "Immediate secondary pass-through detected to obfuscate recipient identity.",
                "impact": "MEDIUM"
            })

        if centrality >= 0.12:
            factors.append({
                "factor": "Network Hub Account",
                "description": f"Beneficiary account exhibits elevated betweenness centrality ({centrality:.3f}), linking multiple clusters.",
                "impact": "HIGH"
            })

        if est_withdrawal_mins <= 35:
            factors.append({
                "factor": "Tight Interception Window",
                "description": f"Predicted cash-out peak in {est_withdrawal_mins} min leaves limited reaction time.",
                "impact": "CRITICAL"
            })

        return factors


# Singleton
_risk_predictor_instance: Optional[CaseRiskPredictor] = None

def get_risk_predictor() -> CaseRiskPredictor:
    global _risk_predictor_instance
    if _risk_predictor_instance is None:
        _risk_predictor_instance = CaseRiskPredictor()
    return _risk_predictor_instance
