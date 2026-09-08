"""
backend/ml/train_xgboost.py — Project DRISHTI (Day 3)
=======================================================
Generates a synthetic labelled dataset and trains an XGBoost regressor
to predict the cash-withdrawal time window (minutes after complaint).

DESIGN RATIONALE:
  We don't have real ground-truth withdrawal times, so we engineer a
  realistic synthetic target variable by encoding known domain patterns:

  1. KYC fraud → criminals have pre-arranged mule accounts → fastest
     withdrawal (mean ~25 min), low spread.
  2. UPI fraud → direct digital transfer, money available quickly →
     mean ~35 min, moderate spread.
  3. Phishing → criminal must move funds across 2–3 hops first →
     slowest (mean ~55 min), high spread.
  4. Higher amounts → criminals wait for large-amount cool-off period → +10 min
  5. Peak hours (18:00–22:00) → ATM queues, higher police activity →
     criminals delay withdrawal → +5 min
  6. Weekends → less police patrol → criminals move faster → -5 min

  All signals have Gaussian noise added (std=8 min) to prevent the model
  from overfitting to a perfectly linear pattern.

OUTPUT:
  models/time_predictor.json  (XGBoost Booster in JSON format)
  models/feature_meta.json    (feature names + encodings for inference)

Run:
  python -m backend.ml.train_xgboost
  (or: python backend/ml/train_xgboost.py from project root)
"""

import os
import json
import random
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

DATA_PATH   = "data/complaints.csv"
MODEL_DIR   = "models"
MODEL_PATH  = os.path.join(MODEL_DIR, "time_predictor.json")
META_PATH   = os.path.join(MODEL_DIR, "feature_meta.json")

os.makedirs(MODEL_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# 1. LOAD COMPLAINT DATA
# ─────────────────────────────────────────────
print("[DRISHTI] Loading complaints.csv ...")
df = pd.read_csv(DATA_PATH, encoding="utf-8")
print(f"  Loaded {len(df)} rows")

# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("[DRISHTI] Engineering features ...")

# Parse timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["hour_of_day"]   = df["timestamp"].dt.hour
df["day_of_week"]   = df["timestamp"].dt.dayofweek  # 0=Mon, 6=Sun
df["is_weekend"]    = (df["day_of_week"] >= 5).astype(int)
df["is_peak_hours"] = df["hour_of_day"].between(18, 22).astype(int)

# Encode fraud_type as integer
FRAUD_TYPE_MAP = {"upi_fraud": 0, "kyc_fraud": 1, "phishing": 2}
df["fraud_type_enc"] = df["fraud_type"].map(FRAUD_TYPE_MAP)

# Log-scale amount (prevents large amounts from dominating)
df["log_amount"] = np.log1p(df["amount"])

# City tier (1=metro, 2=tier2 — affects police response time → criminal risk)
CITY_TIER = {
    "Mumbai": 1, "Delhi": 1, "Bangalore": 1, "Hyderabad": 1, "Chennai": 1,
    "Kolkata": 1, "Pune": 2, "Ahmedabad": 2, "Jaipur": 2, "Lucknow": 2,
}
df["city_tier"] = df["city"].map(CITY_TIER).fillna(2).astype(int)

# ─────────────────────────────────────────────
# 3. SYNTHETIC TARGET VARIABLE
#    withdrawal_minutes = time from complaint to cash withdrawal
#    Domain-driven base + correlated noise
# ─────────────────────────────────────────────
print("[DRISHTI] Generating synthetic target (withdrawal_minutes) ...")

BASE_MINUTES = {0: 35.0, 1: 25.0, 2: 55.0}  # upi / kyc / phishing

withdrawal_minutes = np.zeros(len(df))
for i, row in df.iterrows():
    base = BASE_MINUTES[row["fraud_type_enc"]]

    # Amount effect: +8 min per log-unit above median (criminals hesitate on large sums)
    amount_effect = max(0, (row["log_amount"] - df["log_amount"].median()) * 2.5)

    # Peak hours: criminals delay (higher police visibility)
    peak_effect = 5.0 if row["is_peak_hours"] else 0.0

    # Weekend: criminals are bolder (less police patrol)
    weekend_effect = -4.0 if row["is_weekend"] else 0.0

    # City tier: metro = more cameras/police → criminals delay more
    tier_effect = 3.0 if row["city_tier"] == 1 else 0.0

    # Random noise (realistic variance in human behaviour)
    noise = np.random.normal(0, 8)

    minutes = base + amount_effect + peak_effect + weekend_effect + tier_effect + noise

    # Clamp to realistic range: 5 min (fastest possible) to 120 min
    withdrawal_minutes[i] = float(np.clip(minutes, 5, 120))

df["withdrawal_minutes"] = withdrawal_minutes

print(f"  withdrawal_minutes  mean={df['withdrawal_minutes'].mean():.1f}  "
      f"std={df['withdrawal_minutes'].std():.1f}  "
      f"min={df['withdrawal_minutes'].min():.1f}  "
      f"max={df['withdrawal_minutes'].max():.1f}")

# ─────────────────────────────────────────────
# 4. FEATURE MATRIX
# ─────────────────────────────────────────────
FEATURES = [
    "fraud_type_enc",   # 0/1/2 categorical
    "log_amount",       # log(INR amount)
    "hour_of_day",      # 0–23
    "day_of_week",      # 0–6
    "is_weekend",       # 0/1
    "is_peak_hours",    # 0/1
    "city_tier",        # 1 or 2
]

X = df[FEATURES].values
y = df["withdrawal_minutes"].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"  Train: {len(X_train)}  Test: {len(X_test)}")

# ─────────────────────────────────────────────
# 5. XGBOOST TRAINING
#    Tuned for CPU + small dataset (fast convergence)
# ─────────────────────────────────────────────
print("[DRISHTI] Training XGBoost regressor ...")

dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURES)
dtest  = xgb.DMatrix(X_test,  label=y_test,  feature_names=FEATURES)

params = {
    "objective":        "reg:squarederror",
    "eval_metric":      "mae",
    "max_depth":        4,          # shallow tree: prevents overfitting on synthetic data
    "learning_rate":    0.08,
    "n_estimators":     300,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 5,
    "seed":             42,
    "nthread":          -1,         # use all CPU cores
    "tree_method":      "hist",     # fast CPU training
    "device":           "cpu",      # explicit CPU (no GPU needed)
}

evals_result = {}
booster = xgb.train(
    params,
    dtrain,
    num_boost_round=300,
    evals=[(dtrain, "train"), (dtest, "test")],
    evals_result=evals_result,
    verbose_eval=50,
    early_stopping_rounds=30,
)

# ─────────────────────────────────────────────
# 6. EVALUATION
# ─────────────────────────────────────────────
y_pred = booster.predict(dtest)
mae  = mean_absolute_error(y_test, y_pred)
r2   = r2_score(y_test, y_pred)
print(f"\n[DRISHTI] Test MAE : {mae:.2f} minutes")
print(f"[DRISHTI] Test R2  : {r2:.3f}")
print("[DRISHTI] Feature importances:")
imp = booster.get_score(importance_type="gain")
for feat, score in sorted(imp.items(), key=lambda x: -x[1]):
    print(f"  {feat:<20} {score:.1f}")

# ─────────────────────────────────────────────
# 7. SAVE MODEL + METADATA
# ─────────────────────────────────────────────
booster.save_model(MODEL_PATH)
print(f"\n[DRISHTI] Model saved to: {MODEL_PATH}")

# Save feature metadata so the predictor knows the column order + encodings
meta = {
    "features":       FEATURES,
    "fraud_type_map": FRAUD_TYPE_MAP,
    "city_tier_map":  CITY_TIER,
    "train_rows":     int(len(X_train)),
    "test_mae":       round(float(mae), 2),
    "test_r2":        round(float(r2), 3),
    "target_stats": {
        "mean": round(float(df["withdrawal_minutes"].mean()), 1),
        "std":  round(float(df["withdrawal_minutes"].std()),  1),
        "p10":  round(float(np.percentile(y_pred, 10)), 1),
        "p90":  round(float(np.percentile(y_pred, 90)), 1),
    }
}
with open(META_PATH, "w") as f:
    json.dump(meta, f, indent=2)
print(f"[DRISHTI] Feature metadata saved to: {META_PATH}")

# ─────────────────────────────────────────────
# Quick sanity-check: predict a few manual cases
# ─────────────────────────────────────────────
print("\n[DRISHTI] Sanity check predictions:")
cases = [
    {"name": "UPI, Rs50k, Mon 20:00, Mumbai",  "x": [0, np.log1p(50000),  20, 0, 0, 1, 1]},
    {"name": "KYC, Rs1L,  Sat 10:00, Jaipur",  "x": [1, np.log1p(100000), 10, 5, 1, 0, 2]},
    {"name": "Phish, Rs5k, Wed 14:00, Delhi",  "x": [2, np.log1p(5000),   14, 2, 0, 0, 1]},
    {"name": "UPI,  Rs500, Sun 21:00, Lucknow","x": [0, np.log1p(500),    21, 6, 1, 1, 2]},
]
for case in cases:
    dm = xgb.DMatrix([case["x"]], feature_names=FEATURES)
    pred = float(booster.predict(dm)[0])
    print(f"  {case['name']:<40} -> {pred:.1f} min")
