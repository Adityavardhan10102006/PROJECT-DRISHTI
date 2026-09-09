"""
backend/ml/risk_predictor.py — Project DRISHTI
================================================
Upgraded AI/ML Cybercrime Case Risk Scoring & Rigorous SHAP Explainability.

Features:
  - Multi-class case risk classification (LOW | MEDIUM | HIGH | CRITICAL).
  - Genuine shap.TreeExplainer feature attributions for Explainable AI (XAI).
  - Exposes:
      - feature
      - value
      - shap_value
      - direction ("increases_risk" | "decreases_risk")
      - explanation_source ("shap_tree_explainer" vs "heuristic_fallback")
      - top_positive_features and top_negative_features
  - Calibrated probability distribution across risk tiers.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import shap

from backend.ml.features import (
    FeatureEngineeringPipeline,
    FRAUD_TYPE_MAP,
    CITY_TIER_MAP,
)
from backend.ml.base_predictor import BasePredictor

MODEL_PATH = "models/risk_classifier.joblib"
META_PATH = "models/risk_meta.json"

RISK_TIERS = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH",
    3: "CRITICAL",
}

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


class RiskExplainer:
    """
    Encapsulates SHAP TreeExplainer generation, feature importance ranking,
    and translation of technical ML attributions into human-readable investigative badges.
    """

    def __init__(self, model=None, feature_cols: Optional[List[str]] = None):
        self.model = model
        self.feature_cols = list(feature_cols or FeatureEngineeringPipeline.RISK_FEATURE_NAMES)
        self._explainer = None

    def get_explainer(self):
        """Lazy loader for SHAP TreeExplainer."""
        if self._explainer is None and self.model is not None:
            try:
                self._explainer = shap.TreeExplainer(self.model)
                print("[DRISHTI] SHAP TreeExplainer initialized on demand.")
            except Exception as ex_err:
                print(f"[DRISHTI] Warning: SHAP unavailable ({ex_err})")
                self._explainer = None
        return self._explainer

    def explain(
        self,
        df_x: pd.DataFrame,
        pred_class: int,
        feat_dict: Dict[str, float],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Computes exact SHAP attributions with feature values and directions."""
        explainer = self.get_explainer()
        if explainer is None:
            return [], [], []
        try:
            sv = explainer.shap_values(df_x)
            if isinstance(sv, np.ndarray) and sv.ndim == 3:
                class_sv = sv[0, :, pred_class]
            elif isinstance(sv, list) and len(sv) > pred_class:
                class_sv = sv[pred_class][0]
            else:
                class_sv = np.array(sv).flatten()[:len(self.feature_cols)]

            cols = self.feature_cols
            explanation = []
            pos_list = []
            neg_list = []

            for idx, col in enumerate(cols):
                contrib = float(class_sv[idx])
                val = feat_dict.get(col, 0.0)
                clean_name, human_label, default_desc = FEATURE_LABELS.get(
                    col, (col, col.replace("_", " ").title(), "Model feature attribution")
                )
                direction = "increases_risk" if contrib >= 0 else "decreases_risk"

                if contrib >= 0.08:
                    badge = "🔴"
                elif contrib >= 0.02:
                    badge = "🟠"
                elif contrib >= 0:
                    badge = "🟡"
                else:
                    badge = "🟢"

                item = {
                    "feature": col,
                    "human_label": human_label,
                    "value": round(val, 2) if isinstance(val, float) else val,
                    "shap_value": round(contrib, 4),
                    "importance_weight": round(abs(contrib), 4),
                    "direction": direction,
                    "badge": badge,
                    "description": default_desc,
                }
                explanation.append(item)
                if contrib > 0:
                    pos_list.append(item)
                else:
                    neg_list.append(item)

            explanation.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            pos_list.sort(key=lambda x: x["shap_value"], reverse=True)
            neg_list.sort(key=lambda x: x["shap_value"])

            return explanation, pos_list[:3], neg_list[:2]
        except Exception as e:
            print(f"[DRISHTI] SHAP attribution failed: {e}")
            return [], [], []


class CaseRiskPredictor(BasePredictor):
    """
    Evaluates cybercrime case risk using trained Random Forest / Tree models
    and genuine SHAP TreeExplainer feature attributions.
    """

    def __init__(self, model_path: str = MODEL_PATH, meta_path: str = META_PATH):
        super().__init__(model_path=model_path, meta_path=meta_path)
        self.model = None
        self.meta: Dict[str, Any] = {}
        self.feature_cols: List[str] = FeatureEngineeringPipeline.RISK_FEATURE_NAMES
        self.feature_importances: Dict[str, float] = {}

        self.load_model()
        self.explainer = RiskExplainer(self.model, self.feature_cols)

        print(f"[DRISHTI] AI Risk Classifier loaded successfully (Accuracy: {self.meta.get('metrics', {}).get('accuracy', self.meta.get('accuracy', 'N/A'))})")

    def load_model(self) -> None:
        """Loads pre-trained Random Forest model and metadata from disk."""
        if self.model_path and os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self._model = self.model
            except Exception as e:
                print(f"[DRISHTI] Warning: Could not load risk model ({e})")
                self.model = None

        if self.meta_path and os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
                    self._meta = self.meta
                self.feature_cols = self.meta.get("feature_cols", self.feature_cols)
                self.feature_importances = self.meta.get("feature_importances", {})
            except Exception as e:
                print(f"[DRISHTI] Warning: Could not load risk meta ({e})")

    def _get_explainer(self):
        """Lazy loader for SHAP TreeExplainer delegating to RiskExplainer."""
        return self.explainer.get_explainer()

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
        log_amt = float(np.log1p(max(float(amount or 0.0), 0.0)))
        hour = complaint_dt.hour
        is_weekend = int(complaint_dt.weekday() >= 5)
        ft_enc = FRAUD_TYPE_MAP.get(str(fraud_type).lower(), 0)

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
        Calculates calibrated risk score, tier, and genuine SHAP explanations.
        """
        dt = complaint_dt or datetime.now(timezone.utc)

        feat_dict = self._build_feature_row(
            fraud_type=fraud_type,
            amount=amount,
            hop_count=hop_count,
            centrality=centrality,
            in_degree=in_degree,
            out_degree=out_degree,
            complaint_dt=dt,
            city_tier=city_tier,
            est_withdrawal_mins=est_withdrawal_mins,
        )

        shap_explanation = []
        top_pos = []
        top_neg = []
        df_x = None
        pred_class = 1

        if self.model is not None and self.feature_cols:
            df_x = pd.DataFrame([feat_dict])[self.feature_cols]
            pred_class = int(self.model.predict(df_x)[0])
            pred_probs = self.model.predict_proba(df_x)[0]

            # Weighted expected risk score across class probabilities: [LOW: 15, MED: 42, HIGH: 68, CRITICAL: 92]
            class_weights = np.array([12.0, 42.0, 68.0, 92.0])
            risk_score = float(np.sum(pred_probs * class_weights))
            risk_score = round(float(np.clip(risk_score, 5.0, 99.0)), 1)

            prob_dict = {
                RISK_TIERS[i]: round(float(pred_probs[i]), 3)
                for i in range(len(pred_probs))
            }
        else:
            # Analytical fallback
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
            prob_dict = {"LOW": 0.05, "MEDIUM": 0.85, "HIGH": 0.08, "CRITICAL": 0.02}

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

        # ── Compute SHAP attributions ──
        explanation_source = "heuristic_fallback"
        explainer = self._get_explainer()
        if explainer is not None and df_x is not None:
            shap_explanation, top_pos, top_neg = self._compute_shap_explanation(df_x, pred_class, feat_dict)
            if shap_explanation:
                explanation_source = "shap_tree_explainer"

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
            "top_positive_features": top_pos,
            "top_negative_features": top_neg,
            "model_version": self.meta.get("version", "risk-v2.2"),
            "model_source": "trained_model" if self.model is not None else "heuristic_fallback",
            "dataset_type": self.meta.get("dataset_type", "synthetic_benchmark"),
        }

    def _compute_shap_explanation(
        self,
        df_x: pd.DataFrame,
        pred_class: int,
        feat_dict: Dict[str, float],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Computes exact SHAP attributions with feature values and directions."""
        explainer = self._get_explainer()
        if explainer is None:
            return [], [], []
        try:
            sv = explainer.shap_values(df_x)
            if isinstance(sv, np.ndarray) and sv.ndim == 3:
                class_sv = sv[0, :, pred_class]
            elif isinstance(sv, list) and len(sv) > pred_class:
                class_sv = sv[pred_class][0]
            else:
                class_sv = np.array(sv).flatten()[:len(self.feature_cols)]

            cols = self.feature_cols
            explanation = []
            pos_list = []
            neg_list = []

            for idx, col in enumerate(cols):
                contrib = float(class_sv[idx])
                val = feat_dict.get(col, 0.0)
                clean_name, human_label, default_desc = FEATURE_LABELS.get(
                    col, (col, col.replace("_", " ").title(), "Model feature attribution")
                )
                direction = "increases_risk" if contrib >= 0 else "decreases_risk"

                if contrib >= 0.08:
                    badge = "🔴"
                elif contrib >= 0.02:
                    badge = "🟠"
                elif contrib >= 0:
                    badge = "🟡"
                else:
                    badge = "🟢"

                item = {
                    "feature": col,
                    "human_label": human_label,
                    "value": round(val, 2) if isinstance(val, float) else val,
                    "shap_value": round(contrib, 4),
                    "contribution": round(contrib, 4),
                    "direction": direction,
                    "badge": badge,
                    "description": default_desc,
                    "explanation_source": "shap_tree_explainer",
                }
                explanation.append(item)
                if contrib >= 0:
                    pos_list.append(item)
                else:
                    neg_list.append(item)

            explanation.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            pos_list.sort(key=lambda x: x["shap_value"], reverse=True)
            neg_list.sort(key=lambda x: x["shap_value"])

            return explanation[:6], pos_list[:3], neg_list[:3]
        except Exception as e:
            print(f"[DRISHTI] SHAP TreeExplainer calculation failed: {e}")
            return [], [], []

    def _extract_key_factors(
        self,
        feat_dict: Dict[str, float],
        amount: float,
        hop_count: int,
        centrality: float,
        est_withdrawal_mins: int,
    ) -> List[Dict[str, Any]]:
        factors = []
        if amount > 50000:
            factors.append({
                "feature": "High Loss Volume",
                "description": f"Incident loss of Rs {int(amount):,} exceeds standard retail cybercrime threshold.",
                "impact": "HIGH_POSITIVE",
                "badge": "🔴",
            })
        if hop_count >= 3:
            factors.append({
                "feature": "Layered Multi-Hop Laundering",
                "description": f"{hop_count}-hop rapid fund dispersal detected across intermediary accounts.",
                "impact": "HIGH_POSITIVE",
                "badge": "🔴",
            })
        if centrality >= 0.12:
            factors.append({
                "feature": "Transit Hub Mule Account",
                "description": f"High graph centrality ({centrality:.2f}) indicates syndicate aggregation node.",
                "impact": "MEDIUM_POSITIVE",
                "badge": "🟠",
            })
        if est_withdrawal_mins <= 35:
            factors.append({
                "feature": "Compressed Tactical Window",
                "description": f"Estimated cash-out within {est_withdrawal_mins}m demands immediate patrol dispatch.",
                "impact": "MEDIUM_POSITIVE",
                "badge": "🟠",
            })
        return factors

    def _fallback_shap_explanation(self, top_factors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "feature": f.get("feature", "feature"),
                "human_label": f.get("feature", "Feature"),
                "value": "N/A",
                "shap_value": 0.15 if "HIGH" in f.get("impact", "") else 0.08,
                "contribution": 0.15 if "HIGH" in f.get("impact", "") else 0.08,
                "direction": "increases_risk",
                "badge": f.get("badge", "🟡"),
                "description": f.get("description", ""),
                "explanation_source": "heuristic_fallback",
            }
            for f in top_factors
        ]


_risk_predictor_instance: Optional[CaseRiskPredictor] = None

def get_risk_predictor() -> CaseRiskPredictor:
    global _risk_predictor_instance
    if _risk_predictor_instance is None:
        _risk_predictor_instance = CaseRiskPredictor()
    return _risk_predictor_instance


# Domain / OOP Alias
RiskPredictor = CaseRiskPredictor


if __name__ == "__main__":
    rp = CaseRiskPredictor()
    res = rp.predict("upi_fraud", 85000.0, hop_count=3, centrality=0.25)
    print(f"Risk Score: {res['risk_score']}/100 ({res['risk_level']}), Source: {res['explanation_source']}")
