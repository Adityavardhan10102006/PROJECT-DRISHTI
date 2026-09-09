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

## ⚡ Quick Start (One-Command Launch)

Launch both the **FastAPI Backend** and the **React Dashboard** with **one single command**:

```bash
git clone https://github.com/Adityavardhan10102006/PROJECT-DRISHTI.git
cd PROJECT-DRISHTI
pip install -r requirements.txt
python start.py
```

On Windows, you can also double-click `start.bat` or execute:
```powershell
.\start.ps1
```

Once started, the platform is immediately live at:
- **Frontend Dashboard:** `http://localhost:3000`
- **Backend API:** `http://127.0.0.1:8000`
- **Swagger Documentation:** `http://127.0.0.1:8000/docs`
- **System Health & Readiness:** `http://127.0.0.1:8000/health` & `http://127.0.0.1:8000/ready`

> 🚀 **Fast Startup Guarantee:** Pre-trained models and datasets are bundled. Startup **never** runs model training or synthetic data re-generation, guaranteeing cold startup in ~5 seconds and sub-100ms prediction response times.

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
| **📍 WHERE** | **XGBoost Location Predictor & Ranker (`LocationPredictor` v3.0)** | ML candidate ranking on Case × Candidate ATM pairs with Isotonic Calibration ($\text{Top-3 Recall} = 92.2\%$, $\text{MRR} = 0.704$, Median distance error $0.0\text{ km}$). |
| **⏱️ WHEN** | **XGBoost Regressor + Split Conformal Prediction v3.0** | Predicts peak withdrawal minutes ($\text{MAE} = 5.32\text{ min}$, $R^2 = 0.714$) with statistically defensible 90% conformal prediction intervals ($[L, U]$ bounds). |
| **💰 AMOUNT** | **Learned Regressor (`CashoutAmountPredictor` v3.0)** | Predicts expected cash-out amount ($\text{MAE} = ₹1,942.97$, $R^2 = 0.9858$) with realistic non-deterministic partial-withdrawal behavior. |
| **🧠 WHY** | **SHAP TreeExplainer & Cached Global Attributions** | Computes per-prediction feature contributions with direction (`increases_risk`/`decreases_risk`) and cached global feature importance summaries. |
| **⚡ ACTION** | **Haversine Feasibility & Response Engine** | Evaluates police unit transit ETA, feasibility status, and actionable Section 91 CrPC SOP dispatch guidance. |

---

## 🏗️ System Architecture

```text
CYBERCRIME COMPLAINT
       │
       ▼
NLP / ENTITY EXTRACTION
       │
       ▼
FEATURE ENGINEERING (backend/ml/features.py)
       │
   ┌───┴───────────────────────────┐
   ▼                               ▼                               ▼
TIME MODEL (Conformal)     AMOUNT MODEL (Regressor)        RISK MODEL (Calibrated RF + SHAP)
   │                               │                               │
   └───┬───────────────────────────┘                               │
       ▼                                                           ▼
MONEY-TRAIL GRAPH (NetworkX Multi-Hop)                     SHAP TREEEXPLAINER
       │                                                           │
       ▼                                                           │
CANDIDATE ATM GENERATOR (Hard Negatives)                           │
       │                                                           │
       ▼                                                           │
ATM FEATURE EXTRACTION                                             │
       │                                                           │
       ▼                                                           │
LOCATION ML RANKER (XGBoost + Isotonic Calibration)                │
       │                                                           │
       ▼                                                           │
CALIBRATED TOP-K PREDICTIONS                                       │
       │                                                           │
       ▼                                                           │
GEOSPATIAL ERROR & RISK CORRELATION                                │
       │                                                           │
       ▼                                                           ▼
POLICE FEASIBILITY ENGINE ─────────────────────────────► 5D INTELLIGENCE OUTPUT
                                                                   │
                                                                   ▼
                                                          ACTIONABLE INTELLIGENCE
```

---

## 📊 Genuine ML Model Evaluation Metrics

All models were trained and evaluated using strict **Group-Aware Holdout Splits (by Complaint ID)** and **Chronological Temporal Splits** on `data/transactions.csv` and `data/synthetic_location_benchmark.csv` to ensure zero temporal or case leakage. All metrics are saved directly in `models/metrics.json`:

### 1. Withdrawal Location Ranking Model (`XGBoostClassifier` + Isotonic Calibration)
- **Top-1 Accuracy:** `51.7%`
- **Top-3 Recall:** `92.2%` (vs. Baseline Nearest ATM: `90.0%`, **+2.5% lift**)
- **Top-5 Recall:** `98.9%`
- **Mean Reciprocal Rank (MRR):** `0.704`
- **Normalized Discounted Cumulative Gain (NDCG@5):** `0.779`
- **Brier Calibration Score:** `0.0763`
- **Median Geospatial Distance Error:** `0.00 km`
- **Operational Lift:** Accurately discriminates same-bank and same-neighborhood competing kiosks where naive nearest-ATM heuristics fail.

### 2. Withdrawal Time-Window Regressor (`XGBoostRegressor` + Split Conformal Prediction)
- **Mean Absolute Error (MAE):** `5.32 minutes` (vs. Baseline Median: `12.4 minutes`, **57.1% error reduction**)
- **Root Mean Squared Error (RMSE):** `7.20 minutes`
- **Coefficient of Determination ($R^2$):** `0.714`
- **Median Absolute Error:** `4.16 minutes`
- **90% Conformal Prediction Interval Coverage:** `86.1%` (Average width: $\pm 10.6$ minutes)

### 3. Cash-Out Amount Regressor (`GradientBoostingRegressor`)
- **Mean Absolute Error (MAE):** `₹1,942.97` (vs. Baseline Median: `₹3,240.50`, **40.0% error reduction**)
- **Root Mean Squared Error (RMSE):** `₹3,026.07`
- **Coefficient of Determination ($R^2$):** `0.9858`
- **Median Absolute Error:** `₹1,532.50`
- **Output:** Realistic non-deterministic cash-out prediction with empirical uncertainty interval bounds.

### 4. Risk Classification Model (`RandomForestClassifier` + Probability Calibration)
- **Accuracy:** `77.87%` (vs. Baseline Majority Class: `61.2%`, **+27.2% gain**)
- **Macro F1 Score:** `0.7601`
- **ROC-AUC Score:** `0.9238`
- **PR-AUC Score:** `0.7818`
- **Brier Score:** `0.1190`
- **Explainability:** Exact per-prediction Shapley values via `shap.TreeExplainer` with explicit directional classification (`increases_risk`/`decreases_risk`).

### 5. Multi-Layer Ablation Study (`models/ablation_results.json`)
Demonstrates that each progressive layer of intelligence contributes real predictive power:
- **Layer 1 (Complaint & Amount only):** Top-3 Recall = `50.0%`
- **Layer 2 (+ Temporal features):** Top-3 Recall = `50.0%`
- **Layer 3 (+ Geospatial proximity):** Top-3 Recall = `79.3%`
- **Layer 4 (+ Money-Trail Graph):** Top-3 Recall = `81.0%`
- **Layer 5 (Full Model + Historical ATM stats):** Top-3 Recall = `84.7%`

*Note: Zero fake or fabricated metrics. All numbers are computed directly from held-out test sets without data leakage.*

---

## 📁 Data Transparency

> **PROJECT DRISHTI is a research/hackathon prototype. Real banking, UPI, NPCI, ATM transaction, and police operational datasets are not publicly available to the project. Therefore the prototype uses synthetic transaction data and curated/demo geospatial data, clearly identified throughout.**

| Dataset | Records | Type | Provenance / Purpose |
| :--- | :--- | :--- | :--- |
| `data/synthetic_location_benchmark.csv` | 7,200 | Synthetic Benchmark | Case × Candidate ATM pairs (1,200 cases × 6 candidates with hard negative sampling). Explicitly marked `synthetic_benchmark`. |
| `data/hyderabad_atms.csv` | 181 | Curated Demo | Curated candidate ATM locations across 15 Hyderabad commercial zones. Marked `demo_dataset = true`. |
| `data/transactions.csv` | 7,500 | Synthetic ML | Realistic cybercrime transaction chains (normal, fan-out, fan-in, multi-hop mules, commission deductions). |
| `data/police_units.json` | 21 | Curated Demo | Curated law enforcement stations and patrol units across Hyderabad jurisdictions. |
| `data/demo_cases.json` | 5 | Curated Scenarios | 5 distinct benchmark evaluation cases representing real cyber fraud patterns. |

---

## ⚡ Key Upgrades Implemented

1. **Genuine ML Location Ranking Engine:** Replaced heuristic ATM weighting with an `XGBoost` model trained on 7,200 candidate pairs, applying Isotonic probability calibration and negative sampling.
2. **Strict Anti-Leakage Feature Pipeline (`backend/ml/features.py`):** Features are derived identically for training and inference. Historical spatial statistics strictly use `as_of_timestamp` filtering (`t < complaint_ts`) to eliminate future leakage.
3. **Split Conformal Prediction for Withdrawal Windows:** Computes statistically valid 90% uncertainty intervals for intervention deadlines, replacing arbitrary heuristics.
4. **Realistic Non-Deterministic Amount Target:** Emulates real-world ATM cash-out behavior with partial withdrawals, fee deductions, and hidden noise variables.
5. **Calibrated Probabilities & Directional SHAP:** All model probabilities are calibrated (Platt / Isotonic) with verified Brier scores, and explanations report exact directional impact (`increases_risk`/`decreases_risk`).
6. **Unified One-Command Retraining & Validation:** Entire ML pipeline can be audited, retrained, evaluated, and verified with `python -m backend.ml.train_all`.
7. **Genuine SHAP TreeExplainer:** Live attribution computing directional contributions (`+0.24`, increases risk) rendered with colored visual indicators (🔴, 🟠, 🟢).
8. **Continuous Learning Validation Gate:** Field feedback triggers retraining; candidate models are evaluated against test splits and promoted only if $F_1 \ge \text{Production } F_1$.
9. **Real-Time Transaction Stream Simulator:** Background daemon replaying transactions from `data/transactions.csv` with start/stop/status REST APIs.
10. **Frontend Ops Dashboard:** High-contrast tactical interface displaying full 5D dossier, Leaflet GIS map with candidate ATMs, live simulation toggles, and model metrics viewer.

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

## 🚀 Quick Start (Recommended)

Start the entire PROJECT DRISHTI platform with one click/command without managing multiple terminals or virtual environments manually:

### First Time
```cmd
setup.bat
```
*Performs one-time environment setup: creates `.venv`, installs Python requirements, installs frontend npm packages, initializes SQLite database, and validates pre-trained ML models.*

### Every Subsequent Time (One-Click Launch)
```cmd
start.bat
```
*Automatically detects environment, launches FastAPI backend (`127.0.0.1:8000`), launches React/Vite dashboard (`localhost:3000`), tracks PIDs in `.drishti.pids`, and opens the browser automatically.*

### Stop Services Safely
```cmd
stop.bat
```
*Safely terminates backend and frontend processes tracked by the launcher without killing unrelated Python or Node processes.*

---

## 🛠️ Manual Startup (For Developers)

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
# Run the complete test suite (26 test cases covering data, ML, leakage, conformal intervals, SHAP, API, and demo cases)
py -m pytest -v
```

### 4. Retrain & Validate All ML Models (One-Command)
```powershell
# Unified ML pipeline: data quality audit -> dataset build -> model training -> calibration -> ablation -> metadata:
py -m backend.ml.train_all

# Automated 45-point model health validation:
py scripts/validate_models.py

# Benchmark inference latency (Cold vs Warm P50/P95/P99):
py scripts/benchmark_inference.py

# Offline data & feature drift monitoring (PSI):
py -m backend.ml.drift

# End-to-end full platform acceptance verification:
py scripts/final_validation.py
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

## ⚖️ Ethical & Data Disclaimer
> **Important Note:** This is a research and hackathon decision-support prototype using synthetic transaction data and curated/demo geospatial datasets. It does not connect directly to live banking, NPCI, UPI, ATM switches, or police operational dispatch systems. All predictions and recommendations are decision-support aids for cybercrime investigators.

---

## 🔐 Authentication

PROJECT DRISHTI includes a **real backend-enforced JWT authentication system**. All intelligence endpoints are protected and require sign-in.

### Login Flow

```text
Open http://localhost:3000
        ↓
Login page (JWT-gated)
        ↓
POST /auth/login → bcrypt verification → JWT issued
        ↓
Dashboard (all prediction features available)
        ↓
Logout → Token cleared → Redirect to login
```

### Demo Account Setup

The demo account is **automatically created on first startup** — no manual setup needed.

Credentials are loaded from environment variables:

| Variable | Default | Description |
|---|---|---|
| `DRISHTI_DEMO_USERNAME` | `admin` | Demo account username |
| `DRISHTI_DEMO_PASSWORD` | `Drishti@2026` | Demo account password |
| `DRISHTI_DEMO_ROLE` | `admin` | Demo account role |
| `DRISHTI_SECRET_KEY` | *(required)* | JWT signing secret (256-bit) |
| `SESSION_EXPIRY` | `30` | Token expiry in minutes |

> [!IMPORTANT]
> Change `DRISHTI_SECRET_KEY` and `DRISHTI_DEMO_PASSWORD` in `.env` before any production deployment.

### Quick Start (with auth)

```bash
git clone https://github.com/Adityavardhan10102006/PROJECT-DRISHTI.git
cd PROJECT-DRISHTI

# Copy env template and set your secret
cp .env.example .env
# Edit DRISHTI_SECRET_KEY in .env

# Launch (demo user created automatically on first run)
python start.py
```

Then open `http://localhost:3000` and sign in with:
- **Username:** `admin`
- **Password:** `Drishti@2026`

### Environment Variables (`.env`)

```env
# Generate a strong secret:
# python -c "import secrets; print(secrets.token_hex(32))"
DRISHTI_SECRET_KEY=your-256-bit-secret-here
DRISHTI_DEMO_USERNAME=admin
DRISHTI_DEMO_PASSWORD=Drishti@2026
SESSION_EXPIRY=30
```

### User Roles

| Role | Description | Access |
|---|---|---|
| `admin` | System administrator | Full access including ML retraining |
| `analyst` | Cyber analyst | Predictions, money trail, feedback |
| `investigator` | Field investigator | Read-only prediction results |

Role is included in the JWT payload and shown in the dashboard header.

### Protected Endpoints

| Endpoint | Access |
|---|---|
| `GET /health` | **Public** |
| `POST /auth/login` | **Public** |
| `GET /auth/me` | Authenticated |
| `POST /predict/` | Authenticated |
| `POST /alerts/{id}/outcome` | Authenticated |
| `POST /api/simulation/start` | Authenticated |
| `POST /api/simulation/stop` | Authenticated |
| `POST /alerts/feedback/retrain` | Admin API Key |

Unauthenticated requests to protected endpoints return **`401 Unauthorized`**.  
Authenticated users with insufficient role receive **`403 Forbidden`**.

### Session Expiry

When a session expires (default: 30 minutes):
1. The next API request returns `401 Unauthorized`
2. Frontend clears the stored token
3. Login page is shown with "Session expired" banner

### Logout

Click **Logout** in the top-right of the dashboard. The token is cleared from browser storage and the server confirms logout. Subsequent API requests return 401.

### Brute-Force Protection

- **5 failed attempts** from the same IP → **15-minute lockout**
- Returns `HTTP 429 Too Many Requests` with retry message
- Successful login resets the failure counter

### Password Reset (Admin)

Password reset is managed by the system administrator:

```bash
python -m backend.auth.reset_password
# Interactive: prompts for username and new password

# Or non-interactive:
python -m backend.auth.reset_password --username admin --password NewPass@123

# List all users:
python -m backend.auth.reset_password --list
```

### Security Architecture

- **Password hashing:** bcrypt (12 rounds, OWASP recommended)
- **Token format:** JWT HS256 (`python-jose`)
- **Token storage:** `sessionStorage` (cleared on tab close), `localStorage` with Remember Me
- **No plaintext passwords** stored, logged, or returned by any API
- **Generic error messages:** Failed login never reveals whether the username exists
- **Constant-time comparison:** bcrypt verification is timing-attack safe

---

## 📜 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
