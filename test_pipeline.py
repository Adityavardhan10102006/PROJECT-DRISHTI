"""
test_pipeline.py — Project DRISHTI (Day 2)
===========================================
Sanity-check script: runs 10 sample complaints from complaints.csv
through the NLP extractor + DBSCAN hotspot predictor and prints results.

Run:
    python test_pipeline.py

What to look for:
  [PASS] NLP fraud_type matches the CSV fraud_type column
  [PASS] NLP amount is within 10% of the CSV amount column
  [PASS] Hotspot is within 2.5 km of victim (our ATM generation radius)
  [WARN] Amount is None — regex didn't match this template (note the text)
  [WARN] Fraud type mismatch — keyword weights may need tuning

After reviewing output, if you see systematic mismatches:
  - Edit _FRAUD_KEYWORDS weights in backend/nlp/extractor.py
  - Regenerate complaints.csv with generate_data.py if templates need fixing
"""

import sys
import json
import math
import random
import pandas as pd

# Add project root to path so imports work when run from project dir
sys.path.insert(0, ".")

from backend.nlp.extractor     import ComplaintExtractor
from backend.clustering.hotspot import HotspotPredictor, haversine_km

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
CSV_PATH     = "data/complaints.csv"
NUM_SAMPLES  = 10      # number of complaints to test
RANDOM_SEED  = 99      # for reproducible sample selection
MAX_HOTSPOT_DIST_KM = 2.5  # acceptable hotspot distance from victim

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
print("=" * 65)
print(" DRISHTI Pipeline Test - Day 2")
print("=" * 65)

df = pd.read_csv(CSV_PATH, encoding="utf-8")
print(f"Loaded {len(df)} complaints from {CSV_PATH}\n")

random.seed(RANDOM_SEED)
sample_indices = random.sample(range(len(df)), NUM_SAMPLES)
sample = df.iloc[sample_indices].reset_index(drop=True)

# ─────────────────────────────────────────────
# INIT MODULES
# ─────────────────────────────────────────────
extractor  = ComplaintExtractor()
hotspot    = HotspotPredictor(eps_km=0.5, min_samples=2)

# ─────────────────────────────────────────────
# METRICS ACCUMULATORS
# ─────────────────────────────────────────────
fraud_correct   = 0
amount_close    = 0   # within 10% of true amount
amount_found    = 0   # at least extracted something
hotspot_within  = 0   # within MAX_HOTSPOT_DIST_KM of victim

# ─────────────────────────────────────────────
# RUN EACH SAMPLE
# ─────────────────────────────────────────────
for i, row in sample.iterrows():
    cid        = row["complaint_id"]
    text       = row["complaint_text"]
    true_type  = row["fraud_type"]
    true_amt   = row["amount"]
    vic_lat    = row["victim_lat"]
    vic_lon    = row["victim_lon"]
    city       = row["city"]
    nearby_raw = row["nearby_atms"]

    print(f"--- [{i+1}/{NUM_SAMPLES}] {cid}  ({city}) ---------------------")

    # Truncate long text for display (Hinglish rupee sign may not print on Windows)
    display_text = text[:90].encode("ascii", errors="replace").decode("ascii")
    print(f"  Text    : {display_text}...")

    # ── NLP Extraction ────────────────────────────────────────────
    nlp = extractor.extract(text)

    # Fraud type check
    ft_match = (nlp.fraud_type == true_type)
    if ft_match:
        fraud_correct += 1
        ft_tag = "[PASS]"
    else:
        ft_tag = "[WARN]"

    print(f"  FraudType: {ft_tag} "
          f"extracted={nlp.fraud_type} ({nlp.fraud_type_confidence:.0%})  "
          f"expected={true_type}")

    # Amount check
    amt_tag = "[MISS]"
    if nlp.amount is not None:
        amount_found += 1
        pct_err = abs(nlp.amount - true_amt) / max(true_amt, 1) * 100
        if pct_err <= 10:
            amount_close += 1
            amt_tag = "[PASS]"
        else:
            amt_tag = f"[WARN +{pct_err:.0f}%]"

    print(f"  Amount  : {amt_tag} "
          f"extracted={nlp.amount}  expected={true_amt:.0f}")

    if nlp.transaction_id:
        print(f"  TxnID   : extracted={nlp.transaction_id}")
    if nlp.upi_id:
        print(f"  UPI ID  : {nlp.upi_id}")
    if nlp.phone_number:
        print(f"  Phone   : {nlp.phone_number}")

    # ── DBSCAN Hotspot ────────────────────────────────────────────
    nearby_atms = hotspot.parse_nearby_atms(nearby_raw)
    hs = hotspot.predict_single(nearby_atms, vic_lat, vic_lon)

    if hs:
        dist = haversine_km(vic_lat, vic_lon, hs.lat, hs.lon)
        if dist <= MAX_HOTSPOT_DIST_KM:
            hotspot_within += 1
            hs_tag = "[PASS]"
        else:
            hs_tag = f"[WARN {dist:.1f}km]"

        print(f"  Hotspot : {hs_tag} "
              f"({hs.lat:.4f}, {hs.lon:.4f})  "
              f"r={hs.radius_km:.2f}km  "
              f"conf={hs.confidence:.0%}  "
              f"atms={hs.atm_count}/{len(nearby_atms)}  "
              f"dist_from_victim={dist:.2f}km")
    else:
        print(f"  Hotspot : [MISS] no valid ATM data")

    print()

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
print("=" * 65)
print(" SUMMARY")
print("=" * 65)
print(f"  Samples tested        : {NUM_SAMPLES}")
print(f"  Fraud type accuracy   : {fraud_correct}/{NUM_SAMPLES}  "
      f"({fraud_correct/NUM_SAMPLES:.0%})")
print(f"  Amount extracted      : {amount_found}/{NUM_SAMPLES}  "
      f"({amount_found/NUM_SAMPLES:.0%})")
print(f"  Amount within 10%     : {amount_close}/{NUM_SAMPLES}  "
      f"({amount_close/NUM_SAMPLES:.0%})")
print(f"  Hotspot within {MAX_HOTSPOT_DIST_KM}km  : {hotspot_within}/{NUM_SAMPLES}  "
      f"({hotspot_within/NUM_SAMPLES:.0%})")
print()

# ─────────────────────────────────────────────
# KNOWN ACCURACY LIMITATIONS — read before demo
# ─────────────────────────────────────────────
print("KNOWN LIMITATIONS (tune before demo):")
print("  [!] Amount: templates with 'rupay' in Hinglish extract well.")
print("      Templates where amount is ONLY in the Unicode Rs symbol")
print("      may miss. Check [MISS] rows above.")
print("  [!] Fraud type: complaints mentioning both 'Paytm' and 'KYC'")
print("      may classify as upi_fraud (Paytm weight=1.5 vs KYC=4.0).")
print("      Adjust weights in backend/nlp/extractor.py if needed.")
print("  [~] Hotspot radius reflects synthetic ATM density (3-5 points).")
print("      In production with a real ATM geodatabase, radius shrinks.")
print("      For demo: a 0.5-1.5km radius is realistic for urban India.")
