"""
generate_data.py — Project DRISHTI (Day 1)
==========================================
Generates 5,000 synthetic cybercrime complaints for model training & demo.

Fields per complaint:
  complaint_id      : Unique ID (DRISHTI-00001 … DRISHTI-05000)
  timestamp         : Random datetime within last 6 months
  complaint_text    : Hinglish narrative (varied phrasing per fraud type)
  victim_lat/lon    : Coordinates within major Indian cities
  fraud_type        : upi_fraud | kyc_fraud | phishing
  amount            : Fraudulent amount (INR)
  transaction_id    : Synthetic UPI / ref ID
  bank_account      : Masked account number
  ifsc_code         : Realistic IFSC
  nearby_atms       : JSON list of 3–5 nearby ATM/branch lat-lon pairs
                      (used later for DBSCAN hotspot clustering)

Run:
  python generate_data.py
Output:
  data/complaints.csv
"""

import random
import json
import os
import csv
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# 1. SEED & OUTPUT SETUP
# ─────────────────────────────────────────────
random.seed(42)  # reproducible output

OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "complaints.csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_COMPLAINTS = 5000

# ─────────────────────────────────────────────
# 2. GEOGRAPHIC ANCHORS
#    Major Indian cities with bounding boxes for
#    realistic victim lat/lon generation.
#    (lat_min, lat_max, lon_min, lon_max)
# ─────────────────────────────────────────────
CITIES = {
    "Mumbai":    (18.87, 19.27, 72.77, 72.99),
    "Delhi":     (28.40, 28.88, 76.84, 77.35),
    "Bangalore": (12.83, 13.14, 77.46, 77.78),
    "Hyderabad": (17.28, 17.55, 78.35, 78.60),
    "Chennai":   (12.90, 13.23, 80.15, 80.30),
    "Kolkata":   (22.45, 22.65, 88.30, 88.48),
    "Pune":      (18.43, 18.63, 73.77, 73.97),
    "Ahmedabad": (22.95, 23.12, 72.53, 72.68),
    "Jaipur":    (26.83, 26.98, 75.74, 75.90),
    "Lucknow":   (26.78, 26.96, 80.87, 81.05),
}

# City weights — metros get more complaints (realistic)
CITY_NAMES = list(CITIES.keys())
CITY_WEIGHTS = [20, 18, 15, 12, 10, 8, 6, 5, 4, 2]

# ─────────────────────────────────────────────
# 3. BANK / IFSC POOLS
# ─────────────────────────────────────────────
BANKS = [
    ("SBI",  ["SBIN0", "SBIN1"]),
    ("HDFC", ["HDFC0", "HDFC1"]),
    ("ICICI",["ICIC0", "ICIC1"]),
    ("AXIS", ["UTIB0", "UTIB1"]),
    ("PNB",  ["PUNB0", "PUNB1"]),
    ("BOB",  ["BARB0", "BARB1"]),
    ("Paytm",["PYTM0"]),
    ("PhonePe",["YESB0"]),
]

def random_ifsc():
    """Return a plausible IFSC like HDFC0001234."""
    bank_name, prefixes = random.choice(BANKS)
    prefix = random.choice(prefixes)
    suffix = str(random.randint(1000, 9999))
    return prefix + suffix

def random_account():
    """Return a 12-digit masked account number."""
    return "XXXX" + str(random.randint(10000000, 99999999))

def random_txn_id(fraud_type):
    """Return a realistic transaction/reference ID."""
    if fraud_type == "upi_fraud":
        # UPI transaction reference
        return "UPI" + str(random.randint(100000000000, 999999999999))
    elif fraud_type == "phishing":
        return "REF" + str(random.randint(10000000, 99999999))
    else:  # kyc_fraud
        return "KYC" + str(random.randint(1000000, 9999999))

# ─────────────────────────────────────────────
# 4. COMPLAINT TEXT TEMPLATES (Hinglish)
#    Each list has 10+ varied phrasings to avoid
#    repetitive training data. The NLP parser
#    (Day 2) will extract entities from these.
# ─────────────────────────────────────────────

UPI_TEMPLATES = [
    "Mujhe ek unknown number se call aaya aur unhone bola ki mera UPI limit expire ho raha hai. Maine {amount} rupay transfer kar diye aur paise chale gaye.",
    "Sir, kal raat {amount} rupay mujhse UPI ke zariye fraud ho gaya. Number tha jo mujhe bank ka lagta tha.",
    "Kisi ne mujhe Google Pay pe request bheji aur bol diya ki {amount} receive karne ke liye PIN daalo. Dalne ke baad paise cut ho gaye.",
    "Mere PhonePe account se {amount} rupay bina kisi approval ke transfer ho gaye. Mujhe koi OTP nahi aaya.",
    "UPI fraud hua hai — {amount} rupaye ek anjaan account mein chale gaye. Mera transaction ID {txn_id} hai.",
    "Ek lady ne call karke kaha ki mera paytm verify karna padega. Maine UPI PIN share kiya aur {amount} cut ho gaye.",
    "Sir mera {amount} rupees ka UPI fraud hua. Woh bolte rahe ki ek rupee bhejo verify ke liye, aur phir sara paisa le gaye.",
    "Naya phone liya tha aur UPI setup karte waqt ek fake customer care ka number mila. Unhone {amount} rupees nikal liye.",
    "Online saman kharida tha, delivery boy bana ke aaya, {amount} ka refund dene ke bahane UPI se paise le gaye.",
    "Mujhe ek link aaya Google Pay se, uspe click karne ke baad {amount} rupay account se nikal gaye.",
    "PhonePe par ek request aayi {amount} ki, unhone bola ki yeh cashback hai, collect kar lo — collect karne par paise gaye.",
    "Ek fraud number ne mujhe call karke bola SBI ka fraud department se bol raha hun. {amount} rupay transfer karwa liye.",
]

KYC_TEMPLATES = [
    "Bank ka KYC expire ho raha hai aise message aaya. Ek link pe click kiya aur {amount} rupay account se gaye.",
    "Sir, koi mujhe WhatsApp pe message kiya aur bola ki KYC update nahi hua to account band ho jayega. Maine details de di aur {amount} gaya.",
    "Mujhe ek SMS aaya jisme likha tha: 'Aapka KYC incomplete hai, turant update karein.' Link pe apni details dali aur fraud ho gaya — {amount} rupees.",
    "Kotak bank ka fake agent bana ke aaya aur ghar pe aakar form bhara, baad mein {amount} chori ho gaye.",
    "HDFC KYC update ke liye ek call aaya. Unhone Aadhaar aur PAN maanga. Raat ko {amount} account se nikal gaye.",
    "KYC ke naam pe ek app download karwayi — AnyDesk jaisi — aur phir {amount} apne aap transfer ho gaya.",
    "WhatsApp pe KYC link aaya, bank ka logo bhi tha. Link pe sab fill kiya — {amount} ka nuksan hua.",
    "Paytm KYC ke naam pe ek number ne {amount} rupay ki thaggi ki. Reference number {txn_id}.",
    "Fake UIDAI agent bana ke call kiya. Aadhaar se link karne ke bahane {amount} rupees nikal gaye.",
    "Jan Dhan account mein KYC karne ke liye bolke fraud hua, {amount} rupay gaye meri jan-bachat se.",
]

PHISHING_TEMPLATES = [
    "Ek email aaya jisme likha tha ki mera SBI account suspend hoga. Link pe login kiya aur {amount} gaye.",
    "Sir, kisi ne mere naam ka nakli bank page banaya. Maine wahan password dala aur {amount} transfer ho gaye.",
    "IRCTC ticket cancel ka link aaya, uspe details dali. Baad mein pata chala fraud tha — {amount} rupees gaye.",
    "Amazon ka fake order cancel mail aaya, customer care number dial kiya jo listed tha — {amount} ka fraud.",
    "Ek SMS aaya: 'Congratulations! Aapne {amount} jite hain, claim karo.' Click karne par account se {amount} gaye.",
    "Ek fake income tax refund link share kiya kisi ne. Uspe details dali aur {amount} ka fraud ho gaya.",
    "Netflix subscription renew karne ka SMS aaya. Fake page pe card details dali, {amount} nikal liye.",
    "Lottery jeetne ka message aaya email pe. Processing fee ke roop mein {amount} bheja, koi response nahi.",
    "Mujhe ek QR code bheja gaya jo scan karne par mera {amount} transfer ho gaya.",
    "Fake job offer ke chakkar mein registration fee {amount} bhar di — uske baad number band.",
    "OLX pe bike bech raha tha. Buyer ne payment link bheja, {amount} account se gaye.",
    "Covid relief ke naam pe {amount} maange aur le liye — ek government jaise dikhne wali website pe.",
]

FRAUD_TEMPLATES = {
    "upi_fraud": UPI_TEMPLATES,
    "kyc_fraud": KYC_TEMPLATES,
    "phishing":  PHISHING_TEMPLATES,
}

# ─────────────────────────────────────────────
# 5. NEARBY ATM GENERATOR
#    Simulates 3–5 ATM/branch locations within
#    ~2 km of the victim. DBSCAN will cluster
#    these on Day 2 to find hotspot zones.
# ─────────────────────────────────────────────

def generate_nearby_atms(lat, lon, count=None):
    """
    Return a list of dicts representing nearby ATM/bank branch locations.
    Each is offset from victim coords by a small random delta (≈ 0–2 km).
    1 degree lat ≈ 111 km, so 0.018 degrees ≈ 2 km.
    """
    if count is None:
        count = random.randint(3, 5)

    atms = []
    for _ in range(count):
        delta_lat = random.uniform(-0.018, 0.018)
        delta_lon = random.uniform(-0.018, 0.018)
        atms.append({
            "lat": round(lat + delta_lat, 6),
            "lon": round(lon + delta_lon, 6),
            "type": random.choice(["ATM", "branch", "micro_ATM", "CSP"]),
            "bank": random.choice([b[0] for b in BANKS]),
        })
    return atms

# ─────────────────────────────────────────────
# 6. TIMESTAMP GENERATOR
#    Skewed toward working hours & weekdays
#    to reflect realistic complaint patterns.
# ─────────────────────────────────────────────

BASE_DATE = datetime(2026, 3, 6)   # ~6 months ago from today

def random_timestamp():
    """
    Random datetime within last 6 months, biased toward:
      - Evening hours (18:00–22:00) — peak fraud time
      - Weekdays (Mon–Sat)
    """
    days_back = random.randint(0, 180)
    dt = BASE_DATE + timedelta(days=days_back)

    # 70% chance of peak evening hours
    if random.random() < 0.70:
        hour = random.randint(18, 22)
    else:
        hour = random.randint(9, 17)

    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return dt.replace(hour=hour, minute=minute, second=second)

# ─────────────────────────────────────────────
# 7. AMOUNT DISTRIBUTION
#    Realistic INR fraud amounts by type.
# ─────────────────────────────────────────────

def random_amount(fraud_type):
    """
    UPI fraud: small-medium (₹500 – ₹50,000)
    KYC fraud: medium-large (₹5,000 – ₹2,00,000)
    Phishing:  wide range  (₹1,000 – ₹5,00,000)
    """
    if fraud_type == "upi_fraud":
        return random.randint(500, 50000)
    elif fraud_type == "kyc_fraud":
        return random.randint(5000, 200000)
    else:  # phishing
        return random.randint(1000, 500000)

# ─────────────────────────────────────────────
# 8. MAIN GENERATION LOOP
# ─────────────────────────────────────────────

FIELDNAMES = [
    "complaint_id", "timestamp", "complaint_text",
    "victim_lat", "victim_lon", "city",
    "fraud_type", "amount", "transaction_id",
    "bank_account", "ifsc_code", "nearby_atms",
]

print(f"[DRISHTI] Generating {NUM_COMPLAINTS} synthetic complaints...")

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()

    for i in range(1, NUM_COMPLAINTS + 1):
        # --- Complaint ID ---
        complaint_id = f"DRISHTI-{i:05d}"

        # --- Fraud type (weighted: UPI most common) ---
        fraud_type = random.choices(
            ["upi_fraud", "kyc_fraud", "phishing"],
            weights=[50, 25, 25]
        )[0]

        # --- Location ---
        city = random.choices(CITY_NAMES, weights=CITY_WEIGHTS)[0]
        lat_min, lat_max, lon_min, lon_max = CITIES[city]
        victim_lat = round(random.uniform(lat_min, lat_max), 6)
        victim_lon = round(random.uniform(lon_min, lon_max), 6)

        # --- Amount & IDs ---
        amount = random_amount(fraud_type)
        txn_id = random_txn_id(fraud_type)
        account = random_account()
        ifsc = random_ifsc()

        # --- Complaint text (random template, formatted) ---
        template = random.choice(FRAUD_TEMPLATES[fraud_type])
        complaint_text = template.format(amount=f"₹{amount:,}", txn_id=txn_id)

        # --- Timestamp ---
        ts = random_timestamp()

        # --- Nearby ATMs (serialised as JSON string for CSV storage) ---
        nearby = generate_nearby_atms(victim_lat, victim_lon)
        nearby_json = json.dumps(nearby, ensure_ascii=False)

        writer.writerow({
            "complaint_id":   complaint_id,
            "timestamp":      ts.isoformat(),
            "complaint_text": complaint_text,
            "victim_lat":     victim_lat,
            "victim_lon":     victim_lon,
            "city":           city,
            "fraud_type":     fraud_type,
            "amount":         amount,
            "transaction_id": txn_id,
            "bank_account":   account,
            "ifsc_code":      ifsc,
            "nearby_atms":    nearby_json,
        })

        # Progress indicator every 1000 rows
        if i % 1000 == 0:
            print(f"  >> {i}/{NUM_COMPLAINTS} rows written...")

print(f"[DRISHTI] Done! Saved to: {OUTPUT_FILE}")
print(f"          Columns: {', '.join(FIELDNAMES)}")
