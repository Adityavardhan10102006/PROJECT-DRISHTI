"""
scripts/evaluate_all_models.py — Project DRISHTI
==================================================
Comprehensive Evaluation & Benchmarking Engine.

Computes and saves rigorous evaluation metrics to models/metrics.json:
  - Location Model (Top-1, Top-3, Top-5, Top-10 recall, MRR, NDCG@5, Brier score, Geospatial errors)
  - Time Model (MAE, RMSE, R², Median Absolute Error, Conformal 90% Interval Coverage)
  - Amount Model (MAE, RMSE, R², Median Absolute Error)
  - Risk Model (Accuracy, Precision, Recall, Macro F1, Weighted F1, ROC-AUC, PR-AUC, Brier score)
  - Baselines for each task
  - ML vs Baseline improvements
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.train_all import (
    train_location_model,
    train_time_model,
    train_amount_model,
    train_risk_model,
    RANDOM_SEED,
    MODELS_DIR,
)


def evaluate_all(metrics_output_path: str = "models/metrics.json") -> dict:
    print("=" * 70)
    print(" PROJECT DRISHTI — COMPLETE ML MODEL EVALUATION BENCHMARK")
    print("=" * 70)

    # Re-evaluate models on held-out test splits
    loc_metrics, loc_base = train_location_model()
    time_metrics, time_base = train_time_model()
    amt_metrics, amt_base = train_amount_model()
    risk_metrics, risk_base = train_risk_model()

    central_metrics = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "platform": "Project DRISHTI v2.2 Rigorous ML",
        "random_seed": RANDOM_SEED,
        "risk_model": {
            "model": "RandomForestClassifier",
            "model_type": "RandomForestClassifier",
            "accuracy": risk_metrics["accuracy"],
            "precision": risk_metrics["precision"],
            "recall": risk_metrics["recall"],
            "f1": risk_metrics["f1"],
            "macro_f1": risk_metrics["macro_f1"],
            "roc_auc": risk_metrics["roc_auc"],
            "brier_score": risk_metrics["brier_score"],
            "confusion_matrix": risk_metrics["confusion_matrix"],
            "train_samples": risk_metrics["train_samples"],
            "validation_samples": risk_metrics["validation_samples"],
            "test_samples": risk_metrics["test_samples"],
        },
        "amount_model": {
            "model": "GradientBoostingRegressor",
            "model_type": "GradientBoostingRegressor",
            "mae": amt_metrics["mae"],
            "rmse": amt_metrics["rmse"],
            "r2": amt_metrics["r2"],
            "median_absolute_error": amt_metrics["median_absolute_error"],
            "train_samples": amt_metrics["train_samples"],
            "validation_samples": amt_metrics["validation_samples"],
            "test_samples": amt_metrics["test_samples"],
        },
        "time_model": {
            "model": "XGBoost",
            "model_type": "XGBoost",
            "mae": time_metrics["mae"],
            "rmse": time_metrics["rmse"],
            "r2": time_metrics["r2"],
            "median_absolute_error": time_metrics["median_absolute_error"],
            "conformal_q_90": time_metrics["conformal_q_90"],
            "prediction_interval_coverage": time_metrics["prediction_interval_coverage"],
            "train_samples": time_metrics["train_samples"],
            "validation_samples": time_metrics["validation_samples"],
            "test_samples": time_metrics["test_samples"],
        },
        "location_model": {
            "model": "XGBoostClassifier",
            "model_type": "XGBoostClassifier + IsotonicCalibrator",
            "top1_accuracy": loc_metrics["top1_accuracy"],
            "top3_recall": loc_metrics["top3_recall"],
            "top5_recall": loc_metrics["top5_recall"],
            "top10_recall": loc_metrics["top10_recall"],
            "mrr": loc_metrics["mrr"],
            "ndcg_at_5": loc_metrics["ndcg_at_5"],
            "brier_score": loc_metrics["brier_score"],
            "median_distance_error_km": loc_metrics["median_distance_error_km"],
            "top3_within_3km": loc_metrics["top3_within_3km"],
            "top5_within_5km": loc_metrics["top5_within_5km"],
            "train_samples": loc_metrics["train_samples"],
            "validation_samples": loc_metrics["validation_samples"],
            "test_samples": loc_metrics["test_samples"],
        },
        "baseline": {
            "location": loc_base,
            "time": time_base,
            "amount": amt_base,
            "risk": risk_base,
        },
        "improvement": {
            "location_top3_recall_ml_vs_nearest_atm": f"{loc_metrics['top3_recall']:.1%} vs {loc_base['nearest_atm_top3_recall']:.1%} (+{loc_base['ml_vs_nearest_top3_lift_pct']}%)",
            "time_mae_reduction": f"{time_metrics['mae']}m vs {time_base['baseline_mae']}m ({time_base['baseline_mae_reduction_pct']}% reduction)",
            "amount_mae_reduction": f"Rs {amt_metrics['mae']} vs Rs {amt_base['baseline_mae']} ({amt_base['mae_reduction_pct']}% reduction)",
            "risk_accuracy_gain": f"{risk_metrics['accuracy']:.1%} vs {risk_base['baseline_accuracy']:.1%} (+{risk_base['accuracy_gain_pct']}%)",
        },
    }

    os.makedirs(os.path.dirname(metrics_output_path), exist_ok=True)
    with open(metrics_output_path, "w", encoding="utf-8") as f:
        json.dump(central_metrics, f, indent=2)

    print(f"\n[OK] Evaluation metrics saved to {metrics_output_path}")
    return central_metrics


if __name__ == "__main__":
    evaluate_all()
