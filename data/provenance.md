# Data Provenance & Ethics Architecture — PROJECT DRISHTI

## 1. Ethical & Regulatory Boundary
Project DRISHTI is a hackathon / Smart India Hackathon (SIH26184) prototype engineered for predictive cybercrime intelligence.
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
| `data/demo_cases.json` | 5 Cases | Reference Benchmark | Standardized demonstration & SIH jury evaluation | Representative incident archetypes spanning CRITICAL multi-hop syndicate fraud down to legitimate low-risk retail transactions. |

## 3. Data Integrity & Reproducibility
- Random seed `42` is fixed across data generation and train/val/test splits.
- Data corruption testing (20% noise injection) is maintained to evaluate NLP and regression resilience under missing amounts and corrupted entity tokens.
