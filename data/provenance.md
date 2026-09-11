# Data Provenance & Ethics Architecture — PROJECT DRISHTI

## 1. Ethical & Regulatory Boundary
Project DRISHTI is an advanced predictive cybercrime intelligence framework engineered for law enforcement operations.
In strict adherence to Indian banking regulations (RBI Master Directions on Cyber Security) and law enforcement privacy guidelines (Information Technology Act, DPDP Act 2023):
- **No live or confidential banking feeds** (NPCI UPI, SFMS, RTGS) are accessed or fabricated.
- **No confidential law enforcement databases** (CCTNS, NCRB, I4C live portal) are tapped.
- All transactional and spatial logs are systematically designated as **curated demonstrative or synthetic data** generated under rigorous statistical controls.

## 2. Dataset Classification & Provenance Matrix

| Dataset File | Record Count | Nature | Purpose | Provenance & Construction Method |
|:---|:---:|:---:|:---|:---|
| `data/hyderabad_atms.csv` | 170+ | Curated Demo | Candidate ATM location ranking & geospatial evaluation | Geocoded against 15 major commercial and transport nodes across Hyderabad (Banjara Hills, Hitec City, Begumpet, Charminar, etc.). Explicitly tagged `demo_dataset = true`. |
| `data/transactions.csv` | 7,500+ | Synthetic Modeled | Multi-hop graph analysis & ML model training | Generated with realistic cybercrime distributions: 40% legitimate retail, 60% multi-hop cybercrime laundering chains with 3–8% commission shaving, inter-hop velocity delays (4–22 mins), and transit hub mule reuse. |
| `data/police_units.json` | 21 | Curated Static | Interception feasibility & patrol ETA estimation | Mapped to official Cyber Crime Police Stations (Cyberabad, Hyderabad, Rachakonda) and local law & order PCR vehicles. Contact identifiers are non-personal placeholders. |
| `data/complaints.csv` | 5,000 | Synthetic Labeled | NLP extraction & time regressor training | Generated across 10 Indian metropolitan zones with Hinglish narrative complaint corpora and verified UPI/IFSC entity patterns. |
| `data/demo_cases.json` | 5 Cases | Reference Benchmark | Standardized demonstration & operational evaluation | Representative incident archetypes spanning CRITICAL multi-hop syndicate fraud down to legitimate low-risk retail transactions. |

## 3. Data Integrity & Reproducibility
- Random seed `42` is fixed across data generation and train/val/test splits.
- Data corruption testing (20% noise injection) is maintained to evaluate NLP and regression resilience under missing amounts and corrupted entity tokens.

## 4. Amount Model Feature Dependency & Leakage Audit
- **Canonical Metrics (`models/metrics.json`)**: $R^2 \approx 0.9858$, $\text{MAE} = ₹1,942.97$, $\text{RMSE} = ₹3,807.54$, $\text{Median Absolute Error} = ₹952.79$.
- **Audit Findings**:
  - In financial cybercrime laundering chains, the terminal cash-out withdrawal is physically bounded by the initial incident loss ($A_0$). Intermediary mule accounts shave a small operational commission (3% to 8% per hop):
    $$A_{\text{cashout}} = A_0 \times (1 - c)^{\text{hops} - 1} + \epsilon, \quad \epsilon \sim \mathcal{N}(0, 0.015 A_0)$$
  - Because terminal cash-out amounts in synthetic laundering benchmarks are strictly derived through this commission decay process, the GradientBoostingRegressor learns the mathematical commission curve from `initial_amount` and `hop_count`.
  - This explains the high $R^2 \approx 0.9858$: it is a legitimate consequence of synthetic benchmark generation where stolen principal is preserved across short chains.
  - In real-world institutional deployments with partial account visibility, partial cash-outs, and split fan-outs, empirical $R^2$ will be lower ($\approx 0.70 - 0.85$). DRISHTI discloses this benchmark characteristic openly.

