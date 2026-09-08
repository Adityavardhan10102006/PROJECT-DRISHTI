"""
backend/ml/retrain_feedback.py — Project DRISHTI
==================================================
Continuous Model Improvement Hook:
Loads ground-truth operator validation outcomes from data/feedback_store.jsonl,
merges with base synthetic dataset, and updates the risk classification model.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score
from backend.ml.train_risk_model import generate_synthetic_risk_dataset, FRAUD_TYPE_MAP, RISK_LEVEL_MAP, RANDOM_SEED

FEEDBACK_LOG_PATH = "data/feedback_store.jsonl"
MODEL_OUT_PATH = "models/risk_classifier.joblib"
META_OUT_PATH = "models/risk_meta.json"


def run_continuous_retraining() -> dict:
    """
    Retrains the risk model incorporating accumulated field feedback.
    """
    print("[DRISHTI] Initiating Continuous Model Retraining Loop...")
    base_df = generate_synthetic_risk_dataset(5000)

    # Load feedback logs if available
    feedback_rows = []
    if os.path.exists(FEEDBACK_LOG_PATH):
        with open(FEEDBACK_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        feedback_rows.append(json.loads(line.strip()))
                    except Exception:
                        continue

    feedback_count = len(feedback_rows)
    print(f"[DRISHTI] Ingesting {feedback_count} validated operator records.")

    # Synthesize high-weight samples from validated outcomes
    augmented_records = []
    for fb in feedback_rows:
        intercepted = fb.get("was_intercepted", False)
        mule_confirmed = fb.get("mule_confirmed", False)
        rec_amt = fb.get("recovered_amount") or 35000.0
        
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
            "est_withdrawal_mins": fb.get("actual_withdrawal_minutes") or 35,
            "risk_score": 85.0 if target_level == 3 else 65.0,
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

    clf = GradientBoostingClassifier(
        n_estimators=95,
        learning_rate=0.1,
        max_depth=4,
        random_state=RANDOM_SEED,
    )
    clf.fit(X, y)
    train_acc = accuracy_score(y, clf.predict(X))

    importances = dict(zip(feature_cols, [round(float(v), 4) for v in clf.feature_importances_]))

    joblib.dump(clf, MODEL_OUT_PATH)

    meta = {
        "model_name": "GradientBoostingClassifier",
        "version": f"retrained-feedback-v{feedback_count + 1}",
        "feature_cols": feature_cols,
        "feature_importances": importances,
        "accuracy": round(float(train_acc), 4),
        "feedback_samples_ingested": feedback_count,
        "fraud_type_map": FRAUD_TYPE_MAP,
        "risk_level_map": RISK_LEVEL_MAP,
    }
    with open(META_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "status": "success",
        "message": f"Continuous retraining complete. Ingested {feedback_count} feedback records.",
        "model_version": meta["version"],
        "accuracy": meta["accuracy"],
        "samples_trained": len(combined_df),
    }


if __name__ == "__main__":
    res = run_continuous_retraining()
    print(res)
