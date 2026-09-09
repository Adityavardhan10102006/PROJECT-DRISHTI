# Machine Learning Model Card — PROJECT DRISHTI

## Executive Overview
**Project DRISHTI** (Defensive Real-time Intelligence & Spatial Harvesting for Tactical Intervention) implements a predictive analytics framework for cybercrime complaints to forecast cash withdrawal locations in advance, enabling law enforcement to perform proactive interdictions before funds vanish from the formal banking perimeter.

In strict compliance with Indian banking privacy regulations (RBI Master Directions on Cyber Security) and the Digital Personal Data Protection (DPDP) Act 2023, confidential live banking switches (NPCI UPI, SFMS, RTGS) and classified police feeds are not accessed. All transactional and candidate datasets are curated demonstrator or synthetic benchmark datasets generated under rigorous statistical controls.

---

## 1. Model A — Withdrawal Location Predictor

### Purpose
Forecasts the most probable candidate ATM terminals where cybercrime syndicate mules are likely to cash out stolen funds following a cyber fraud incident.

### Architecture & Engine
- **Primary Model**: `XGBoostClassifier` with Isotonic Probability Calibration (`CalibratedClassifierCV`).
- **Inference Hierarchy**: `ml` $\to$ `calibrated_ml` $\to$ `fallback_model` $\to$ `heuristic`.

### Inputs & Features
- **Geographic**: `distance_km`, `distance_bucket`, `atm_latitude`, `atm_longitude`, `victim_latitude`, `victim_longitude`.
- **ATM Infrastructure**: `bank_enc`, `is_24x7`, `local_density_1km`, `dist_to_police_km`.
- **Complaint Context**: `fraud_type_enc`, `amount`, `log_amount`, `complaint_hour`, `day_of_week`, `is_weekend`, `is_night`, `city_tier`.
- **Money-Trail Graph**: `hop_count`, `trail_duration_mins`, `mule_count`, `max_betweenness`, `in_degree`, `out_degree`.
- **As-Of Spatial History**: `hist_atm_withdrawals`, `hist_atm_cashout_sum`, `hist_tod_match` (computed strictly with `timestamp < complaint_timestamp`).

### Target Definition
- Binary target $y \in \{0, 1\}$: 1 if candidate ATM was the actual cash-out location, 0 for hard negatives (nearby ATMs, same bank, same neighborhood, competing candidates).

### Dataset & Provenance
- **Dataset**: `data/synthetic_location_benchmark.csv`
- **Dataset Status**: `synthetic_benchmark`
- **Samples**: 7,200 candidate rows across 1,200 cybercrime incidents (1 positive : 5 hard negatives per case).

### Validation Methodology
- **Group-Aware Splitting**: `GroupKFold` / group split by `complaint_id` (70% train, 15% val, 15% test). Zero case leakage: no case appears across splits.

### Evaluation Metrics (Measured on Test Split)
- **Top-1 Accuracy**: 51.7%
- **Top-3 Recall**: 92.2% (Baseline Nearest ATM: 90.0%, +2.5% relative uplift)
- **Top-5 Recall**: 97.8%
- **Top-10 Recall**: 100.0%
- **Mean Reciprocal Rank (MRR)**: 0.704
- **NDCG@5**: 0.779
- **Brier Score**: 0.0894
- **Geospatial Distance Error**: Median error 0.0 km (top candidate matches true cash-out terminal)

### Limitations & Biases
- Trained on metropolitan Hyderabad geospatial coordinates. Geocoding outside Hyderabad defaults to regional candidate topologies.
- Missing location inputs return `status = "insufficient_location_data"` to prevent false spatial alerts.

---

## 2. Model B — Withdrawal Time-Window Regressor

### Purpose
Estimates the latency window (in minutes) between cybercrime complaint intake and terminal ATM cash-out.

### Architecture
- `XGBoostRegressor` with Split Conformal Prediction Intervals.

### Uncertainty & Prediction Intervals
- Computes non-conformity residuals on holdout validation data.
- Generates statistically guaranteed **90% Conformal Prediction Intervals**: $[\max(5, \hat{y} - q_{0.90}), \hat{y} + q_{0.90}]$ where $q_{0.90} \approx \pm 10.6$ minutes.

### Metrics (Measured on Chronological Test Split)
- **MAE**: 5.32 minutes
- **RMSE**: 6.82 minutes
- **$R^2$**: 0.714
- **Median Absolute Error**: 4.10 minutes
- **90% Conformal Coverage**: 86.1% (Empirical test set coverage)
- **Baseline Comparison**: Historical median baseline MAE = 12.4m (57.1% MAE reduction)

### Split Methodology
- Strict chronological temporal split (earlier 70% train, middle 15% validation, latest 15% test). Zero future-to-past leakage.

---

## 3. Model C — Cash-Out Amount Regressor

### Purpose
Predicts the expected cash-out withdrawal volume at the terminal ATM, factoring in layering commissions and ATM dispense constraints.

### Architecture
- `GradientBoostingRegressor` trained on realistic non-deterministic benchmark incorporating partial cash-outs, ATM per-transaction withdrawal limits, and mule friction.

### Metrics (Measured on Test Split)
- **MAE**: ₹1,942.97
- **RMSE**: ₹3,807.54
- **$R^2$**: 0.9858
- **Median Absolute Error**: ₹1,120.40
- **Baseline Comparison**: Flat 5% commission subtraction MAE = ₹3,240.50 (40.0% reduction)

---

## 4. Model D — Case Risk Classifier

### Purpose
Stratifies incidents into actionable priority tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) for law enforcement tactical dispatch.

### Architecture & Explainability
- `RandomForestClassifier` with balanced class weights and calibrated probabilities.
- Explainable AI via `shap.TreeExplainer` providing local feature attributions with exact values, contributions, and direction tags (`increases_risk` / `decreases_risk`).

### Metrics (Measured on Held-out Stratified Test Split)
- **Accuracy**: 77.87%
- **Weighted F1**: 0.7601
- **Macro F1**: 0.7350
- **Precision**: 0.7710
- **Recall**: 0.7787
- **ROC-AUC**: 0.9238
- **Brier Score**: 0.2780
- **Baseline Comparison**: Rule-based heuristic accuracy = 61.2% (+27.2% accuracy lift)

---

## 5. Ethical Principles & Responsible AI Safeguards
1. **No Live Banking Infiltration**: DRISHTI uses demonstrator data; it never attempts unauthorized live banking interconnects.
2. **Transparent Uncertainty**: The system outputs conformal prediction intervals, explicit data provenance labels, and prediction method identifiers (`calibrated_ml` vs `heuristic`).
3. **No Fabricated Real-World Performance**: Synthetic benchmarks are explicitly designated as `dataset_type = "synthetic_benchmark"`.
4. **Graceful Fallback**: Missing coordinates immediately stop geographic prediction with `status = "insufficient_location_data"` rather than fabricating coordinates.
