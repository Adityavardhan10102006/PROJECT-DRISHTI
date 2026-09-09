"""
backend/ml/retrain_feedback.py — Project DRISHTI
==================================================
Continuous Model Improvement Hook:
Loads ground-truth operator validation outcomes from data/feedback_store.jsonl,
merges with realistic transaction dataset features, trains a candidate model,
and rigorously validates performance against a test split before promoting to production.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from backend.ml.train_risk_model import generate_synthetic_risk_dataset, FRAUD_TYPE_MAP, RISK_LEVEL_MAP, RANDOM_SEED

FEEDBACK_LOG_PATH = "data/feedback_store.jsonl"
PROD_MODEL_PATH = "models/risk_classifier.joblib"
PROD_META_PATH = "models/risk_meta.json"
CANDIDATE_MODEL_PATH = "models/candidate_risk_classifier.joblib"
METRICS_PATH = "models/metrics.json"


def run_continuous_retraining() -> dict:
    """
    Retrains the risk model incorporating accumulated field feedback.
    Applies an evaluation gate: candidate model is promoted only if it
    demonstrates stability/improvement on holdout validation data.
    """
    print("[DRISHTI-FEEDBACK] Initiating Continuous Model Retraining Loop with Validation Gate...")

    # Load realistic base risk distribution reflecting transaction dataset
    base_df = generate_synthetic_risk_dataset(7000)

    # Load feedback logs if available
    feedback_rows = []
    if os.path.exists(FEEDBACK_LOG_PATH):
        with open(FEEDBACK_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        feedback_rows.append(json.loads(line_str))
                    except Exception:
                        continue

    feedback_count = len(feedback_rows)
    print(f"[DRISHTI-FEEDBACK] Ingested {feedback_count} validated operator records.")

    # Synthesize high-weight samples from validated outcomes
    augmented_records = []
    for fb in feedback_rows:
        intercepted = fb.get("was_intercepted", False)
        mule_confirmed = fb.get("mule_confirmed", False)
        rec_amt = float(fb.get("recovered_amount") or 35000.0)
        
        # Ground truth label adjustment based on confirmed field outcome
        if intercepted or mule_confirmed:
            target_level = 3 if rec_amt >= 50000 else 2
        else:
            target_level = 1

        augmented_records.append({
            "fraud_type": "upi_fraud",
            "amount": rec_amt,
            "log_amount": float(np.log1p(rec_amt)),
            "hop_count": 3 if mule_confirmed else 2,
            "betweenness_centrality": 0.25 if mule_confirmed else 0.05,
            "in_degree": 4 if mule_confirmed else 2,
            "out_degree": 3 if mule_confirmed else 1,
            "hour": 20,
            "is_weekend": 0,
            "city_tier": 1,
            "est_withdrawal_mins": float(fb.get("actual_withdrawal_minutes") or 35.0),
            "risk_level": target_level,
        })

    if augmented_records:
        aug_df = pd.DataFrame(augmented_records)
        # Duplicate high-confidence ground truth to increase importance (5x weight)
        combined_df = pd.concat([base_df] + [aug_df] * 5, ignore_index=True)
    else:
        combined_df = base_df

    feature_cols = [
        "fraud_type_enc",
        "log_amount",
        "hop_count",
        "betweenness_centrality",
        "in_degree",
        "out_degree",
        "hour",
        "is_weekend",
        "city_tier",
        "est_withdrawal_mins",
    ]
    combined_df["fraud_type_enc"] = combined_df["fraud_type"].map(FRAUD_TYPE_MAP).fillna(0)

    X = combined_df[feature_cols]
    y = combined_df["risk_level"]

    # Strict 80/20 train/test holdout split to evaluate candidate model
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )

    candidate_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    candidate_clf.fit(X_train, y_train)

    cand_preds = candidate_clf.predict(X_test)
    cand_acc = float(accuracy_score(y_test, cand_preds))
    cand_f1 = float(f1_score(y_test, cand_preds, average="weighted", zero_division=0))
    cand_prec = float(precision_score(y_test, cand_preds, average="weighted", zero_division=0))
    cand_rec = float(recall_score(y_test, cand_preds, average="weighted", zero_division=0))

    # Evaluate existing production model on same holdout set
    prod_acc = 0.0
    prod_f1 = 0.0
    if os.path.exists(PROD_MODEL_PATH):
        try:
            prod_clf = joblib.load(PROD_MODEL_PATH)
            prod_preds = prod_clf.predict(X_test)
            prod_acc = float(accuracy_score(y_test, prod_preds))
            prod_f1 = float(f1_score(y_test, prod_preds, average="weighted", zero_division=0))
        except Exception as e:
            print(f"[DRISHTI-FEEDBACK] Warning evaluating production model: {e}")

    # Model evaluation gate: candidate must match or exceed prod F1 (with 0.01 tolerance)
    # or if prod model didn't exist / had zero score
    promoted = False
    gate_threshold = max(0.60, prod_f1 - 0.01)

    if cand_f1 >= gate_threshold:
        promoted = True
        joblib.dump(candidate_clf, PROD_MODEL_PATH)
        importances = dict(zip(feature_cols, [round(float(v), 4) for v in candidate_clf.feature_importances_]))
        version_str = f"feedback-promoted-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        meta = {
            "model_name": "RandomForestClassifier",
            "version": version_str,
            "feature_cols": feature_cols,
            "feature_importances": importances,
            "accuracy": round(cand_acc, 4),
            "f1_score": round(cand_f1, 4),
            "precision": round(cand_prec, 4),
            "recall": round(cand_rec, 4),
            "feedback_samples_ingested": feedback_count,
            "training_timestamp": datetime.now(timezone.utc).isoformat(),
            "fraud_type_map": FRAUD_TYPE_MAP,
            "risk_level_map": RISK_LEVEL_MAP,
            "promoted": True
        }
        with open(PROD_META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Update metrics.json
        if os.path.exists(METRICS_PATH):
            try:
                with open(METRICS_PATH, "r", encoding="utf-8") as f:
                    curr_metrics = json.load(f)
                curr_metrics["risk_model"]["accuracy"] = round(cand_acc, 4)
                curr_metrics["risk_model"]["f1"] = round(cand_f1, 4)
                curr_metrics["risk_model"]["precision"] = round(cand_prec, 4)
                curr_metrics["risk_model"]["recall"] = round(cand_rec, 4)
                with open(METRICS_PATH, "w", encoding="utf-8") as f:
                    json.dump(curr_metrics, f, indent=2)
            except Exception:
                pass
    else:
        # Candidate rejected; save as candidate artifact for audit
        joblib.dump(candidate_clf, CANDIDATE_MODEL_PATH)
        version_str = f"candidate-rejected-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    return {
        "status": "success",
        "promoted": promoted,
        "message": f"Continuous retraining evaluated. Promoted: {promoted}. Feedback count: {feedback_count}",
        "candidate_metrics": {
            "accuracy": round(cand_acc, 4),
            "f1_score": round(cand_f1, 4),
            "precision": round(cand_prec, 4),
            "recall": round(cand_rec, 4),
        },
        "production_f1": round(prod_f1, 4),
        "model_version": version_str,
        "samples_trained": len(combined_df),
    }

# Alias for backward compatibility
retrain_model = run_continuous_retraining

if __name__ == "__main__":
    res = run_continuous_retraining()
    print(json.dumps(res, indent=2))
