# Project DRISHTI 🛡️
### 5D Cybercrime Intelligence, Hotspot Tracking & Tactical Interception Platform
**Smart India Hackathon 2026 | Problem Statement ID: SIH26184**  
**Ministry of Home Affairs (MHA) | Theme: Blockchain & Cybersecurity**

---

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Leaflet](https://img.shields.io/badge/GIS-Leaflet-199900.svg?style=flat&logo=leaflet)](https://leafletjs.com)
[![SHAP](https://img.shields.io/badge/XAI-SHAP_TreeExplainer-FF0055.svg?style=flat)](https://shap.readthedocs.io)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost_v2.0-FF6600.svg?style=flat)](https://xgboost.readthedocs.io)
[![Scikit-Learn](https://img.shields.io/badge/Models-RandomForest_&_GBR-F7931E.svg?style=flat&logo=scikit-learn)](https://scikit-learn.org)
[![NetworkX](https://img.shields.io/badge/Graph-NetworkX_Multi--Hop-00599C.svg?style=flat)](https://networkx.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Problem Statement Overview (SIH26184)

In digital financial cybercrimes across India (such as **UPI scams, KYC phishing, job frauds, investment task scams, and SIM swap schemes**), organized syndicates siphon stolen money through layered networks of **mule bank accounts** before physically cashing out at automated teller machines (ATMs).

### The Critical 30–60 Minute "Golden Window"
- **The Challenge:** Once stolen money is withdrawn in cash from an ATM, the recovery probability plummets to near **zero**. Law enforcement currently relies on reactive, post-incident bank trail statements that often take days or weeks to obtain through formal notice procedures.
- **The Solution:** **Project DRISHTI** (*Detection and Real-time Intelligence for Surveillance, Hotspot Tracking, and Interception*) provides an automated, sub-second predictive intelligence framework that transforms incoming cybercrime complaints and money trails into **5D Actionable Intelligence** before the criminal completes the cash-out.

---

## 🎯 The 5D Predictive Intelligence Framework

Project DRISHTI delivers complete, explainable 5D intelligence to cyber cells and police field units:

| Dimension | Engine / Methodology | Operational Output |
| :--- | :--- | :--- |
| **📍 WHERE** | **Curated Candidate ATM Evaluation (`data/hyderabad_atms.csv`)** | Dynamically ranks real ATM candidates using distance, bank liquidity, 24x7 operation, and commercial density. No random coordinate jitter. |
| **⏱️ WHEN** | **XGBoost Regressor v2.0** ($\text{MAE} = 6.13\text{ min}$) | Predicts earliest, peak, and latest cash-out time window with countdown and tactical time margin. |
| **💰 AMOUNT** | **Learned Regressor (`CashoutAmountPredictor`)** ($\text{MAE} \approx ₹513, R^2 = 0.9997$) | Predicts expected cash-out amount with empirical uncertainty prediction intervals ($[L, U]$ bounds). |
| **🧠 WHY** | **SHAP TreeExplainer ($TreeExplainer$)** | Computes exact Shapley feature attributions with human-readable badges (🔴, 🟠, 🟢) explaining what drove the risk score. |
| **⚡ ACTION** | **Haversine Feasibility & Response Engine** | Pairs the case with real patrol units (`data/police_units.json`), computes vehicle ETA, and generates SOP dispatch instructions. |

---

## 🏗️ System Architecture

```text
Complaint
    ↓
NLP Extraction
    ↓
Transaction Lookup
    ↓
Transaction Graph (NetworkX Multi-Hop)
    ↓
ML Prediction (Risk · Time · Amount)
    ↓
WHERE / WHEN / AMOUNT
    ↓
SHAP TreeExplainer (Feature Attributions)
    ↓
Hyderabad ATM Candidates (Top-K Ranking)
    ↓
Response Feasibility (Police ETA & Margin)
    ↓
5D Intelligence Synthesis (WHERE · WHEN · AMOUNT · WHY · ACTION)
    ↓
Feedback & Validation Gate Retraining Loop
```

---

## 📊 Genuine ML Model Evaluation Metrics

All models were evaluated using strict **70% Train / 15% Validation / 15% Test holdout splits** on `data/transactions.csv` (7,500 records) to prevent data leakage. Metrics are saved in `models/metrics.json`:

### 1. Risk Classification Model (`RandomForestClassifier`, 100 Trees)
- **Accuracy:** `80.29%` (Validation) / `78.48%` (Test)
- **Weighted F1 Score:** `0.7788`
- **ROC-AUC Score:** `0.9148`
- **Explainability:** Fully compatible with `shap.TreeExplainer` for per-case feature contributions.

### 2. Cash-Out Amount Regressor (`GradientBoostingRegressor`)
- **Mean Absolute Error (MAE):** `₹513.04`
- **Root Mean Squared Error (RMSE):** `₹1,045.75`
- **Coefficient of Determination ($R^2$):** `0.9997`
- **Output:** Point prediction with empirical lower and upper uncertainty bounds.

### 3. Withdrawal Time-Window Regressor (`XGBoostRegressor`)
- **Mean Absolute Error (MAE):** `6.13 minutes`
- **Root Mean Squared Error (RMSE):** `7.64 minutes`
- **$R^2$ Score:** `0.7108`
- **Window Accuracy ($\le 10\text{m}$):** `79.9%`

*Note: Zero fake or fabricated accuracy numbers. All numbers are computed from holdout test sets.*

---

## 📁 Data Transparency

> **PROJECT DRISHTI is a research/hackathon prototype. Real banking, UPI, NPCI, ATM transaction, and police operational datasets are not publicly available to the project. Therefore the prototype uses synthetic transaction data and curated/demo geospatial data.**

| Dataset | Records | Type | Provenance / Purpose |
| :--- | :--- | :--- | :--- |
| `data/hyderabad_atms.csv` | 181 | Curated Demo | Curated candidate ATM locations across 15 Hyderabad commercial zones. Marked `demo_dataset = true`. |
| `data/transactions.csv` | 7,500 | Synthetic ML | Realistic cybercrime transaction chains (normal, fan-out, fan-in, multi-hop mules, commission deductions). |
| `data/police_units.json` | 21 | Curated Demo | Curated law enforcement stations and patrol units across Hyderabad jurisdictions. |
| `data/demo_cases.json` | 5 | Curated Scenarios | 5 distinct benchmark evaluation cases representing real cyber fraud patterns. |

---

## ⚡ Key Upgrades Implemented

1. **Replaced Synthetic Jitter with Curated Candidate ATMs:** Prediction evaluates actual candidate ATM branches from `data/hyderabad_atms.csv` using dynamic distance, volume liquidity, and 24x7 operational criteria.
2. **Multi-Hop Money Trail Engine:** NetworkX queries `data/transactions.csv` first for matching transaction flows, calculating in-degree, out-degree, velocity, and betweenness centrality.
3. **Learned Cash-Out Amount Regression:** Upgraded from static percentage deduction to a trained `GradientBoostingRegressor` providing point estimates and confidence intervals.
4. **Genuine SHAP TreeExplainer:** Live attribution computing directional contributions (`+0.24`, increases risk) rendered with colored visual indicators (🔴, 🟠, 🟢).
5. **Continuous Learning Validation Gate:** Field feedback triggers retraining; candidate models are evaluated against test splits and promoted only if $F_1 \ge \text{Production } F_1$.
6. **Real-Time Transaction Stream Simulator:** Background daemon replaying transactions from `data/transactions.csv` with start/stop/status REST APIs.
7. **Frontend Ops Dashboard:** High-contrast tactical interface displaying full 5D dossier, Leaflet GIS map with candidate ATMs, live simulation toggles, and model metrics viewer.

---

## 🧪 Demonstration Cases (`data/demo_cases.json`)

The platform includes 5 standardized demo cases for presentation:

1. **CASE-001 (UPI High-Value Rapid Divert):**  
   - *Scenario:* Stolen ₹85,000 transferred via 3 rapid mule hops.  
   - *Expected Outcome:* **CRITICAL Risk (80+)**, peak window ~35 min, top candidate SBI ATM Banjara Hills, Excellent dispatch margin.
2. **CASE-002 (Low-Value Phishing Probe):**  
   - *Scenario:* ₹4,500 small ticket diversion.  
   - *Expected Outcome:* **LOW / MEDIUM Risk**, routine monitoring recommendation.
3. **CASE-003 (Mule-Ring Fan-Out Syndicate):**  
   - *Scenario:* ₹1,75,000 siphoned and distributed across multiple intermediary accounts.  
   - *Expected Outcome:* **CRITICAL Risk**, high betweenness centrality flagged.
4. **CASE-004 (Night-Time Cyber Skimming):**  
   - *Scenario:* ₹48,000 transfer at 02:30 AM targeting 24x7 ATM kiosks.  
   - *Expected Outcome:* **HIGH Risk**, prioritized for 24x7 off-site ATM patrol intercept.
5. **CASE-005 (Legitimate Business Transaction):**  
   - *Scenario:* Day-time single-hop vendor settlement.  
   - *Expected Outcome:* **LOW Risk (<25)**, no alert dispatch.

---

## 🚀 How to Run the Project

### Prerequisites
- Python 3.10+ (tested on Python 3.14 on Windows)
- Node.js 18+ and npm

### 1. Backend Setup & Startup
```powershell
# In the project root directory:
# Install dependencies
py -m pip install -r requirements.txt

# Start the FastAPI server
py -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### 2. Frontend Dashboard Setup & Startup
In a separate terminal:
```cmd
cd frontend
npm install
npm run dev
```
- Open `http://localhost:3000` in your browser.

### 3. Run Automated Tests
```powershell
# Run the complete test suite (14 test cases covering data, ML, SHAP, API, and demo cases)
py -m pytest tests/test_master_suite.py -v
```

### 4. Retrain Models
```powershell
# Retrain all ML models (Risk, Amount, Time) from scratch:
py -m backend.ml.train_models

# Run continuous feedback retraining loop with validation gate:
py -m backend.ml.retrain_feedback
```

---

## 📋 Hackathon Presentation Demo Flow

1. **Launch Dashboard:** Open `http://localhost:3000`. Point out the system health badge and click **📊 ML Metrics** in the top bar to show genuine, non-fabricated evaluation metrics.
2. **Ingest Cybercrime Case:** In the left panel, click **Quick Load Demo** (`UPI (Hyderabad)` or `KYC (Delhi)`) and submit.
3. **Inspect 5D Dossier (Right Panel):**
   - **WHERE:** Highlight the primary candidate ATM in Banjara Hills / Hitec City.
   - **WHEN:** Show the predicted withdrawal window countdown and police ETA margin.
   - **AMOUNT:** Demonstrate the learned cash-out regression range (e.g. ₹81,100 with $[L, U]$ confidence interval).
   - **WHY:** Show SHAP explainability badges (🔴 High Transaction Amount, 🔴 Multi-Hop Trail).
   - **ACTION:** Review the automatic Section 91 CrPC SOP and click **📋 Copy Dispatch SOP**.
4. **Interactive GIS Map (Center):** Click **Focus on Map** to zoom to the candidate ATM cluster and view the police patrol unit vector.
5. **Real-Time Simulation Mode:** Click **▶ START SIMULATION** in the top nav to demonstrate streaming cybercrime transactions.
6. **Validate Field Outcome:** Click **⚖️ Validate Outcome**, log an interception with recovered funds, and demonstrate continuous learning.

---

## ⚠️ Limitations
Explicitly listed in accordance with research ethics and hackathon transparency:
- **Synthetic transaction dataset:** Transaction trails and banking logs are generated under statistical cybercrime distributions rather than live NPCI/banking feeds.
- **Demo ATM dataset:** Candidate ATMs are curated across 15 commercial hubs in Hyderabad (`data/hyderabad_atms.csv`) rather than an RBI nationwide terminal API.
- **Static police-unit data:** Patrol unit positions represent curated station houses and mobile patrol units (`data/police_units.json`) rather than live GPS AVL telemetry.
- **Estimated response times:** Transit ETAs use Haversine and urban velocity models rather than commercial live-traffic routing APIs.
- **No direct banking integration:** The platform generates investigative guidance and protocol requisitions; it does NOT directly freeze bank accounts.
- **No live UPI/NPCI stream:** The platform operates on complaint ingestion and simulated stream replays rather than live bank gateway switches.
- **No live police dispatch:** The system provides decision-support priority recommendations rather than automated CAD emergency 112 dispatch.
- **Prototype-level model validation:** All machine learning models are validated on held-out test splits under experimental prototype conditions.

---

## 📜 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
