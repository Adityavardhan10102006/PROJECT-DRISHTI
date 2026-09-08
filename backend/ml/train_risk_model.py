"""
backend/ml/train_risk_model.py — Project DRISHTI
==================================================
Trains an AI/ML Risk Classification & Scoring model on synthetic labeled
cybercrime data reflecting realistic Indian cybercrime syndicate patterns:
  - Higher amounts (> ₹50,000) correlate strongly with professional mule rings.
  - Multi-hop transaction chains (3+ hops) indicate deliberate layering.
  - Accounts with high graph betweenness centrality indicate syndicate hubs.
  - Peak hours (18:00 - 23:00) and short cash-out windows indicate high urgency.

Uses scikit-learn GradientBoostingClassifier (100% CPU, no GPU/paid APIs).
Saves:
  - models/risk_classifier.joblib
  - models/risk_meta.json
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)
MODEL_OUT_PATH = os.path.join(MODELS_DIR, "risk_classifier.joblib")
META_OUT_PATH = os.path.join(MODELS_DIR, "risk_meta.json")

FRAUD_TYPE_MAP = {"upi_fraud": 0, "kyc_fraud": 1, "phishing": 2}
RISK_LEVEL_MAP = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}


def generate_synthetic_risk_dataset(num_samples: int = 6000) -> pd.DataFrame:
    """
    Generates a realistic synthetic dataset for cybercrime case risk classification.
    """
    fraud_types = np.random.choice(["upi_fraud", "kyc_fraud", "phishing"], size=num_samples, p=[0.50, 0.25, 0.25])
    
    # Amounts by fraud type
    amounts = []
    for ft in fraud_types:
        if ft == "upi_fraud":
            amt = np.random.exponential(scale=18000) + 500
        elif ft == "kyc_fraud":
            amt = np.random.exponential(scale=45000) + 5000
        else:
            amt = np.random.exponential(scale=65000) + 2000
        amounts.append(min(float(amt), 500000.0))
    amounts = np.array(amounts)

    # Graph properties
    hop_counts = np.random.choice([1, 2, 3, 4], size=num_samples, p=[0.25, 0.40, 0.25, 0.10])
    centrality = np.clip(np.random.beta(a=0.8, b=3.5, size=num_samples), 0.0, 1.0)
    in_degree = np.random.poisson(lam=3.0, size=num_samples) + 1
    out_degree = np.random.poisson(lam=2.5, size=num_samples) + 1

    # Temporal & Spatial properties
    hour_probs = np.array([
        0.02, 0.01, 0.01, 0.01, 0.01, 0.01,  # 00-05
        0.02, 0.03, 0.04, 0.05, 0.06, 0.07,  # 06-11
        0.07, 0.06, 0.06, 0.06, 0.07, 0.08,  # 12-17
        0.09, 0.07, 0.05, 0.03, 0.02, 0.01   # 18-23
    ], dtype=float)
    hour_probs = hour_probs / hour_probs.sum()
    hours = np.random.choice(range(24), size=num_samples, p=hour_probs)
    is_weekend = np.random.choice([0, 1], size=num_samples, p=[0.72, 0.28])
    city_tiers = np.random.choice([1, 2, 3], size=num_samples, p=[0.55, 0.35, 0.10])
    est_withdrawal_mins = np.clip(np.random.normal(loc=40, scale=18, size=num_samples), 10, 110)

    # Ground truth risk scoring formula with deliberate realistic correlations
    # Risk Score in [0, 100]
    log_amt = np.log1p(amounts)
    norm_amt = (log_amt - 6.0) / 7.0  # ~ 0 to 1
    
    latent_risk = (
        0.28 * norm_amt +
        0.24 * (hop_counts / 4.0) +
        0.20 * centrality +
        0.12 * (out_degree / 10.0) +
        0.10 * ((120 - est_withdrawal_mins) / 110.0) +
        0.06 * (hours >= 18).astype(float) +
        np.random.normal(0, 0.05, size=num_samples)
    )
    latent_risk = np.clip(latent_risk, 0.0, 1.0)
    risk_score_100 = latent_risk * 100.0

    # Categorical labels:
    # 0: LOW (< 35)
    # 1: MEDIUM (35 - 55)
    # 2: HIGH (55 - 75)
    # 3: CRITICAL (>= 75)
    labels = np.zeros(num_samples, dtype=int)
    labels[(risk_score_100 >= 35) & (risk_score_100 < 55)] = 1
    labels[(risk_score_100 >= 55) & (risk_score_100 < 75)] = 2
    labels[risk_score_100 >= 75] = 3

    df = pd.DataFrame({
        "fraud_type": fraud_types,
        "amount": amounts,
        "log_amount": log_amt,
        "hop_count": hop_counts,
        "betweenness_centrality": centrality,
        "in_degree": in_degree,
        "out_degree": out_degree,
        "hour": hours,
        "is_weekend": is_weekend,
        "city_tier": city_tiers,
        "est_withdrawal_mins": est_withdrawal_mins,
        "risk_score": risk_score_100,
        "risk_level": labels,
    })
    return df


def train_and_save_model():
    print("=" * 60)
    print(" Project DRISHTI — Training AI/ML Cybercrime Risk Model")
    print("=" * 60)
    
    df = generate_synthetic_risk_dataset(7000)
    print(f"Generated synthetic training set: {len(df)} samples")
    print(df["risk_level"].value_counts().rename(index=RISK_LEVEL_MAP))

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

    df["fraud_type_enc"] = df["fraud_type"].map(FRAUD_TYPE_MAP)
    X = df[feature_cols]
    y = df["risk_level"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y)

    print("\nTraining GradientBoostingClassifier on CPU...")
    clf = GradientBoostingClassifier(
        n_estimators=90,
        learning_rate=0.1,
        max_depth=4,
        random_state=RANDOM_SEED,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Evaluation:")
    print(f"Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["LOW", "MEDIUM", "HIGH", "CRITICAL"]))

    # Feature importances
    importances = dict(zip(feature_cols, [round(float(v), 4) for v in clf.feature_importances_]))
    print("\nFeature Importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feat:<25}: {imp * 100:.2f}%")

    # Save artifacts
    joblib.dump(clf, MODEL_OUT_PATH)
    print(f"\nSaved model weights to: {MODEL_OUT_PATH}")

    meta = {
        "model_name": "GradientBoostingClassifier",
        "version": "1.0-risk",
        "feature_cols": feature_cols,
        "feature_importances": importances,
        "accuracy": round(float(acc), 4),
        "fraud_type_map": FRAUD_TYPE_MAP,
        "risk_level_map": RISK_LEVEL_MAP,
    }
    with open(META_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved feature metadata to: {META_OUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    train_and_save_model()
